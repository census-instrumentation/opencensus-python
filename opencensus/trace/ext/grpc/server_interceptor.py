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
import collections
import logging

import grpc

from opencensus.trace import attributes_helper
from opencensus.trace import tracer as tracer_module
from opencensus.trace import execution_context
from opencensus.trace.ext import grpc as oc_grpc
from opencensus.trace.propagation import binary_format

ATTRIBUTE_COMPONENT = 'COMPONENT'
ATTRIBUTE_ERROR_NAME = 'ERROR_NAME'
ATTRIBUTE_ERROR_MESSAGE = 'ERROR_MESSAGE'

RpcRequestInfo = collections.namedtuple(
    'RPCRequestInfo', ('request', 'context')
)
RpcResponseInfo = collections.namedtuple(
    'RPCCallbackInfo', ('request', 'context', 'response', 'exc')
)


class RpcMethodHandlerWrapper(object):
    """Wraps a grpc RPCMethodHandler and records the variables about the
     execution context and response
    """

    def __init__(
        self, handler, pre_handler_callbacks=None, post_handler_callbacks=None
    ):
        """
        :param handler: instance of RpcMethodHandler

        :param pre_handler_callbacks: iterable of callbacks that accept an
         instance of RpcRequestInfo that are called before the server handler

        :param post_handler_callbacks: iterable of callbacks that accept an
         instance of RpcResponseInfo that are called after the server
         handler finishes execution
        """
        self.handler = handler
        self._pre_handler_callbacks = pre_handler_callbacks or []
        self._post_handler_callbacks = post_handler_callbacks or []

    def proxy(self, prop_name):
        def _wrapper(request, context, *args, **kwargs):
            for callback in self._pre_handler_callbacks:
                callback(RpcRequestInfo(request, context))
            exc = None
            response = None
            try:
                response = getattr(
                    self.handler, prop_name
                )(request, context, *args, **kwargs)
            except Exception as e:
                logging.error(e)
                exc = e
                raise
            finally:
                for callback in self._post_handler_callbacks:
                    callback(RpcResponseInfo(request, context, response, exc))
            return response

        return _wrapper

    def __getattr__(self, item):
        if item in (
            'unary_unary', 'unary_stream', 'stream_unary', 'stream_stream'
        ):
            return self.proxy(item)
        return getattr(self.handler, item)


class OpenCensusServerInterceptor(grpc.ServerInterceptor):
    def __init__(self, sampler=None, exporter=None):
        self.sampler = sampler
        self.exporter = exporter

    def _start_server_span(self, rpc_request_info):
        metadata = rpc_request_info.context.invocation_metadata()
        span_context = None

        if metadata is not None:
            propagator = binary_format.BinaryFormatPropagator()
            metadata_dict = dict(metadata)
            trace_header = metadata_dict.get(oc_grpc.GRPC_TRACE_KEY)

            span_context = propagator.from_header(trace_header)

        tracer = tracer_module.Tracer(span_context=span_context,
                                      sampler=self.sampler,
                                      exporter=self.exporter)

        span = tracer.start_span(name='grpc_server')
        tracer.add_attribute_to_current_span(
            attribute_key=attributes_helper.COMMON_ATTRIBUTES.get(
                ATTRIBUTE_COMPONENT),
            attribute_value='grpc')

        execution_context.set_opencensus_tracer(tracer)
        execution_context.set_current_span(span)

    def _end_server_span(self, rpc_response_info):
        tracer = execution_context.get_opencensus_tracer()
        if rpc_response_info.exc is not None:
            tracer.add_attribute_to_current_span(
                attributes_helper.COMMON_ATTRIBUTES.get(
                    ATTRIBUTE_ERROR_MESSAGE),
                str(rpc_response_info.exc))
        tracer.end_span()

    def intercept_handler(self, continuation, handler_call_details):
        return RpcMethodHandlerWrapper(
            continuation(handler_call_details),
            pre_handler_callbacks=[self._start_server_span],
            post_handler_callbacks=[self._end_server_span]
        )

    def intercept_service(self, continuation, handler_call_details):
        return self.intercept_handler(continuation, handler_call_details)
