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

import sys
import logging

# Note: Currently the interceptor support for Python in grpc is not available
# yet, this is based on the code in the pull request in the grpc repository.
from opencensus.trace import grpc
from opencensus.trace.grpc import grpc_ext
from opencensus.trace.propagation import binary_format
from opencensus.trace import request_tracer

from opencensus.trace.enums import Enum


class OpenCensusServerInterceptor(grpc_ext.UnaryUnaryServerInterceptor,
                                  grpc_ext.UnaryStreamServerInterceptor,
                                  grpc_ext.StreamUnaryServerInterceptor,
                                  grpc_ext.StreamStreamServerInterceptor):

    def __init__(self, sampler=None, reporter=None):
        self.sampler = sampler
        self.reporter = reporter

    def _start_server_span(self, tracer, servicer_context, method):
        span = tracer.start_span(name=str(method))
        span.add_label(label_key='component', label_value='grpc')
        span.kind = Enum.SpanKind.RPC_SERVER
        return span

    def intercept_handler(self, request_type, handler, method, request,
                          servicer_context):
        metadata = servicer_context.invocation_metadata()
        span_context = None

        if metadata is not None:
            propagator = binary_format.BinaryFormatPropagator()
            metadata_dict = dict(metadata)
            trace_header = metadata_dict[grpc.GRPC_TRACE_KEY]
            span_context = propagator.from_header(trace_header)

        tracer = request_tracer.RequestTracer(span_context=span_context,
                                              sampler=self.sampler,
                                              reporter=self.reporter)

        tracer.start_trace()

        with self._start_server_span(tracer, servicer_context, method) as span:
            response = None
            span.name = '[gRPC_server][{}]{}'.format(request_type, str(method))
            try:
                response = handler(request, servicer_context)
            except:
                e = sys.exc_info()[0]
                logging.error(e)
                raise

        tracer.end_trace()
        return response

    def intercept_unary_unary_handler(self, handler, method, request,
                                      servicer_context):
        return self.intercept_handler(grpc.UNARY_UNARY, handler, method,
                                      request, servicer_context)

    def intercept_unary_stream_handler(self, handler, method, request,
                                       servicer_context):
        return self.intercept_handler(grpc.UNARY_STREAM, handler, method,
                                      request, servicer_context)

    def intercept_stream_unary_handler(self, handler, method, request_iterator,
                                       servicer_context):
        return self.intercept_handler(grpc.STREAM_UNARY, handler, method,
                                      request_iterator, servicer_context)

    def intercept_stream_stream_handler(self, handler, method,
                                        request_iterator,
                                        servicer_context):
        return self.intercept_handler(grpc.STREAM_STREAM, handler, method,
                                      request_iterator, servicer_context)
