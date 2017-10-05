# Copyright 2016 Google Inc.
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

import logging
import grpc
import six
import sys

from opencensus.trace import grpc
from opencensus.trace.grpc import grpc_ext
from opencensus.trace.propagation import binary_format
from opencensus.trace import execution_context

from opencensus.trace.enums import Enum

log = logging.getLogger(__name__)


class OpenCensusClientInterceptor(grpc_ext.UnaryUnaryClientInterceptor,
                                  grpc_ext.UnaryStreamClientInterceptor,
                                  grpc_ext.StreamUnaryClientInterceptor,
                                  grpc_ext.StreamStreamClientInterceptor):

    def __init__(self, tracer=None):
        if tracer is None:
            tracer = execution_context.get_opencensus_tracer()

        self._tracer = tracer
        self._propagator = binary_format.BinaryFormatPropagator()

    def _start_client_span(self, method):
        log.info('Start client span')
        span = self._tracer.start_span(name='[gRPC]{}'.format(str(method)))
        span.add_label(label_key='component', label_value='grpc')
        span.kind = Enum.SpanKind.RPC_CLIENT
        return span

    def _trace_async_result(self, result):
        result.add_done_callback(self._future_done_callback())

        return result

    def _future_done_callback(self):
        def callback(future_response):
            code = future_response.code()

            if code != grpc.StatusCode.OK:
                span.add_label('error in response', str(code))

            response = future_response.result()
            self._tracer.end_span()

        return callback

    def intercept_call(self, request_type, invoker, method, request, **kwargs):
        metadata = getattr(kwargs, 'metadata', ())

        with self._start_client_span(method) as span:
            span_context = self._tracer.span_context
            header = self._propagator.to_header(span_context)
            grpc_trace_metadata = {
                grpc.GRPC_TRACE_KEY: header,
            }
            metadata = metadata + tuple(six.iteritems(grpc_trace_metadata))

            span.name = '[gRPC_client][{}]{}'.format(request_type, str(method))

            try:
                result = invoker(method, request, metadata=metadata, **kwargs)
            except:
                e = sys.exc_info()[0]
                span.add_label('error', str(e))
                raise

        return result

    def intercept_future(
            self, request_type, invoker, method, request, **kwargs):
        metadata = getattr(kwargs, 'metadata', ())

        with self._start_client_span(method) as span:
            span_context = self._tracer.span_context
            header = self._propagator.to_header(span_context)
            grpc_trace_metadata = {
                grpc.GRPC_TRACE_KEY: header,
            }
            metadata = metadata + tuple(six.iteritems(grpc_trace_metadata))

            span.name = '[gRPC_client][{}]{}'.format(request_type, str(method))

            try:
                result = invoker(method, request, metadata=metadata, **kwargs)
            except:
                e = sys.exc_info()[0]
                span.add_label('error', str(e))
                raise

        return self._trace_async_result(result)

    def intercept_unary_unary_call(self, invoker, method, request, **kwargs):
        return self.intercept_call(
            grpc.UNARY_UNARY, invoker, method, request, **kwargs)

    def intercept_unary_unary_future(self, invoker, method, request, **kwargs):
        return self.intercept_future(
            grpc.UNARY_UNARY, invoker, method, request, **kwargs)

    def intercept_unary_stream_call(self, invoker, method, request, **kwargs):
        return self.intercept_call(
            grpc.UNARY_STREAM, invoker, method, request, **kwargs)

    def intercept_stream_unary_call(self, invoker, method, request_iterator,
                                    **kwargs):
        return self.intercept_call(
            grpc.STREAM_UNARY, invoker, method, request_iterator, **kwargs)

    def intercept_stream_unary_future(self, invoker, method, request_iterator,
                                      **kwargs):
        return self.intercept_future(
            grpc.STREAM_UNARY, invoker, method, request_iterator, **kwargs)

    def intercept_stream_stream_call(self, invoker, method, request_iterator,
                                     **kwargs):
        return self.intercept_call(
            grpc.STREAM_STREAM, invoker, method, request_iterator, **kwargs)
