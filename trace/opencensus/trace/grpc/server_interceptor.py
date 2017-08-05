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
from opencensus.trace.grpc import grpc_ext
from opencensus.trace.propagation import text_format
from opencensus.trace.tracer import context_tracer

from opencensus.trace.enums import Enum


class OpenCensusServerInterceptor(grpc_ext.UnaryServerInterceptor):

    def __init__(self, sampler=None, reporter=None):
        self.sampler = sampler
        self.reporter = reporter

    def _start_server_span(self, tracer, servicer_context, method):
        logging.warn('test server span')

        span = tracer.start_span(name=str(method))
        span.add_label(label_key='component', label_value='grpc')
        span.kind = Enum.SpanKind.RPC_SERVER
        return span

    def intercept_unary(self, request, servicer_context, server_info, handler):
        metadata = servicer_context.invocation_metadata()
        span_context = None

        if metadata is not None:
            span_context = text_format.from_carrier(dict(metadata))

        tracer = context_tracer.ContextTracer(span_context=span_context,
                                              sampler=self.sampler,
                                              reporter=self.reporter)

        tracer.start_trace()

        with self._start_server_span(tracer, servicer_context,
                                server_info.full_method) as span:
            response = None
            span.add_label(label_key='metadata', label_value=str(metadata))
            try:
                response = handler(request)
            except:
                e = sys.exc_info()[0]
                logging.error(e)
                raise

        tracer.end_trace()
        return response
