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
import six
import sys

from opencensus.trace.grpc import grpc_ext
from opencensus.trace.propagation import text_format

from opencensus.trace.enums import Enum

class OpenCensusClientInterceptor(grpc_ext.UnaryClientInterceptor):

    def __init__(self, tracer):
        self._tracer = tracer

    def _start_client_span(self, method):
        logging.warn('test client span')
        span = self._tracer.start_span(name=str(method))
        span.add_label(label_key='component', label_value='grpc')
        span.kind = Enum.SpanKind.RPC_CLIENT
        return span

    def intercept_unary(self, method, request, metadata, invoker):
        span_context = self._tracer.span_context

        headers = {}
        headers = text_format.to_carrier(span_context, headers)

        if metadata is None:
            metadata = ()
        else:
            metadata = tuple(metadata)

        metadata = metadata + tuple(six.iteritems(headers))

        with self._start_client_span(method) as span:
            span.add_label(label_key='metadata', label_value=str(metadata))

            try:
                result = invoker(request, metadata)
            except:
                e = sys.exc_info()[0]
                span.add_label('error', str(e))
                raise

            return result
