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
from opencensus.trace import attributes_helper, execution_context
from opencensus.trace import span as span_module
from opencensus.trace import stack_trace as stack_trace
from opencensus.trace import status, time_event
from opencensus.trace import tracer as tracer_module
from opencensus.trace.propagation import binary_format

COMPONENT = attributes_helper.COMMON_ATTRIBUTES['COMPONENT']
ERROR_NAME = attributes_helper.COMMON_ATTRIBUTES['ERROR_NAME']
ERROR_MESSAGE = attributes_helper.COMMON_ATTRIBUTES['ERROR_MESSAGE']

HTTP_HOST = attributes_helper.COMMON_ATTRIBUTES['HTTP_HOST']
HTTP_METHOD = attributes_helper.COMMON_ATTRIBUTES['HTTP_METHOD']
HTTP_PATH = attributes_helper.COMMON_ATTRIBUTES['HTTP_PATH']
HTTP_ROUTE = attributes_helper.COMMON_ATTRIBUTES['HTTP_ROUTE']
HTTP_URL = attributes_helper.COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = attributes_helper.COMMON_ATTRIBUTES['HTTP_STATUS_CODE']
GRPC_METHOD = attributes_helper.GRPC_ATTRIBUTES['GRPC_METHOD']

RECV_PREFIX = 'Recv'

grpc_http_status_mapping = {
    grpc.StatusCode.OK : 200,
    grpc.StatusCode.FAILED_PRECONDITION : 400,
    grpc.StatusCode.INVALID_ARGUMENT : 400,
    grpc.StatusCode.OUT_OF_RANGE : 400,
    grpc.StatusCode.UNAUTHENTICATED : 401,
    grpc.StatusCode.PERMISSION_DENIED : 403,
    grpc.StatusCode.NOT_FOUND : 404,
    grpc.StatusCode.ABORTED : 409,
    grpc.StatusCode.ALREADY_EXISTS : 409,
    grpc.StatusCode.RESOURCE_EXHAUSTED : 429,
    grpc.StatusCode.CANCELLED : 499,
    grpc.StatusCode.UNKNOWN : 500,
    grpc.StatusCode.INTERNAL : 500,
    grpc.StatusCode.DATA_LOSS : 500,
    grpc.StatusCode.UNIMPLEMENTED : 501,
    grpc.StatusCode.UNAVAILABLE : 503,
    grpc.StatusCode.DEADLINE_EXCEEDED : 504
}

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

                    http_status_code = _convert_grpc_code_to_http_status_code(
                        servicer_context._state.code
                    )
                    span.add_attribute(HTTP_STATUS_CODE, http_status_code)

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

        grpc_call_details = servicer_context._rpc_event.call_details
        grpc_host = grpc_call_details.host.decode('utf-8')
        grpc_method = grpc_call_details.method.decode('utf-8')

        tracer.add_attribute_to_current_span(
            COMPONENT, 'grpc'
        )
        tracer.add_attribute_to_current_span(
            GRPC_METHOD, grpc_method
        )

        tracer.add_attribute_to_current_span(
            HTTP_HOST, grpc_host
        )
        tracer.add_attribute_to_current_span(
            HTTP_METHOD, 'POST'
        )
        tracer.add_attribute_to_current_span(
            HTTP_ROUTE, grpc_method
        )
        tracer.add_attribute_to_current_span(
            HTTP_PATH, grpc_method
        )
        tracer.add_attribute_to_current_span(
            HTTP_URL, 'grpc://' + grpc_host + grpc_method
        )

        execution_context.set_opencensus_tracer(tracer)
        execution_context.set_current_span(span)
        return span

def _convert_grpc_code_to_http_status_code(grpc_state_code):
    """
    Converts a gRPC state code into the corresponding HTTP response status.
    See: https://github.com/googleapis/googleapis/blob/master/google/rpc/code.proto
    """
    if grpc_state_code is None:
        return 200
    else:
        return grpc_http_status_mapping.get(grpc_state_code, 500)

def _add_exc_info(span):
    exc_type, exc_value, tb = sys.exc_info()
    span.add_attribute(ERROR_MESSAGE, str(exc_value))
    span.stack_trace = stack_trace.StackTrace.from_traceback(tb)
    span.status = status.Status(
        code=code_pb2.UNKNOWN,
        message=str(exc_value)
    )
    span.add_attribute(HTTP_STATUS_CODE, 500)


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
