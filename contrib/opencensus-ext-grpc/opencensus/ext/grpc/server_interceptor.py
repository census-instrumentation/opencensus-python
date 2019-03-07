# Copyright 2017, OpenCensus Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import sys

import grpc
from google.rpc import code_pb2

from opencensus.ext import grpc as oc_grpc
from opencensus.ext.grpc import utils as grpc_utils
from opencensus.trace import attributes_helper
from opencensus.trace import execution_context
from opencensus.trace import span as span_module
from opencensus.trace import stack_trace as stack_trace
from opencensus.trace import status
from opencensus.trace import time_event
from opencensus.trace import tracer as tracer_module
from opencensus.trace.propagation import binary_format

ATTRIBUTE_COMPONENT = 'COMPONENT'
ATTRIBUTE_ERROR_NAME = 'ERROR_NAME'
ATTRIBUTE_ERROR_MESSAGE = 'ERROR_MESSAGE'
RECV_PREFIX = 'Recv'


class OpenCensusServerInterceptor(grpc.ServerInterceptor):
    def __init__(self, sampler=None, exporter=None):
        self.sampler = sampler
        self.exporter = exporter

    def intercept_service(self, continuation, handler_call_details):
        def trace_wrapper(behavior, request_streaming, response_streaming):
            def new_behavior(request_or_iterator, servicer_context):
                span = self._start_server_span(servicer_context)
                try:
                    if request_streaming:
                        request_or_iterator = grpc_utils.wrap_iter_with_message_events(  # noqa: E501
                            request_or_response_iter=request_or_iterator,
                            span=span,
                            message_event_type=time_event.Type.RECEIVED
                        )
                    else:
                        grpc_utils.add_message_event(
                            proto_message=request_or_iterator,
                            span=span,
                            message_event_type=time_event.Type.RECEIVED,
                        )
                    # invoke the original rpc behavior
                    response_or_iterator = behavior(request_or_iterator,
                                                    servicer_context)
                    if response_streaming:
                        response_or_iterator = grpc_utils.wrap_iter_with_message_events(  # noqa: E501
                            request_or_response_iter=response_or_iterator,
                            span=span,
                            message_event_type=time_event.Type.SENT
                        )
                        response_or_iterator = grpc_utils.wrap_iter_with_end_span(  # noqa: E501
                            response_or_iterator)
                    else:
                        grpc_utils.add_message_event(
                            proto_message=response_or_iterator,
                            span=span,
                            message_event_type=time_event.Type.SENT,
                        )
                except Exception:
                    _add_exc_info(span)
                    raise
                finally:
                    # if the response is unary, end the span here. Otherwise
                    # it will be closed when the response iter completes
                    if not response_streaming:
                        execution_context.get_opencensus_tracer().end_span()
                return response_or_iterator

            return new_behavior

        return _wrap_rpc_behavior(
            continuation(handler_call_details),
            trace_wrapper
        )

    def _start_server_span(self, servicer_context):
        metadata = servicer_context.invocation_metadata()
        span_context = None

        if metadata is not None:
            propagator = binary_format.BinaryFormatPropagator()
            metadata_dict = dict(metadata)
            trace_header = metadata_dict.get(oc_grpc.GRPC_TRACE_KEY)

            span_context = propagator.from_header(trace_header)

        tracer = tracer_module.Tracer(span_context=span_context,
                                      sampler=self.sampler,
                                      exporter=self.exporter)

        span = tracer.start_span(
            name=_get_span_name(servicer_context)
        )

        span.span_kind = span_module.SpanKind.SERVER
        tracer.add_attribute_to_current_span(
            attribute_key=attributes_helper.COMMON_ATTRIBUTES.get(
                ATTRIBUTE_COMPONENT),
            attribute_value='grpc')

        execution_context.set_opencensus_tracer(tracer)
        execution_context.set_current_span(span)
        return span


def _add_exc_info(span):
    exc_type, exc_value, tb = sys.exc_info()
    span.add_attribute(
        attributes_helper.COMMON_ATTRIBUTES.get(
            ATTRIBUTE_ERROR_MESSAGE),
        str(exc_value)
    )
    span.stack_trace = stack_trace.StackTrace.from_traceback(tb)
    span.status = status.Status(
        code=code_pb2.UNKNOWN,
        message=str(exc_value)
    )


def _wrap_rpc_behavior(handler, fn):
    """Returns a new rpc handler that wraps the given function"""
    if handler is None:
        return None

    if handler.request_streaming and handler.response_streaming:
        behavior_fn = handler.stream_stream
        handler_factory = grpc.stream_stream_rpc_method_handler
    elif handler.request_streaming and not handler.response_streaming:
        behavior_fn = handler.stream_unary
        handler_factory = grpc.stream_unary_rpc_method_handler
    elif not handler.request_streaming and handler.response_streaming:
        behavior_fn = handler.unary_stream
        handler_factory = grpc.unary_stream_rpc_method_handler
    else:
        behavior_fn = handler.unary_unary
        handler_factory = grpc.unary_unary_rpc_method_handler

    return handler_factory(
        fn(behavior_fn, handler.request_streaming,
           handler.response_streaming),
        request_deserializer=handler.request_deserializer,
        response_serializer=handler.response_serializer
    )


def _get_span_name(servicer_context):
    """Generates a span name based off of the gRPC server rpc_request_info"""
    method_name = servicer_context._rpc_event.call_details.method[1:]
    if isinstance(method_name, bytes):
        method_name = method_name.decode('utf-8')
    method_name = method_name.replace('/', '.')
    return '{}.{}'.format(RECV_PREFIX, method_name)
