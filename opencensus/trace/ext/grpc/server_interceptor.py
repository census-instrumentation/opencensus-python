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

import grpc
import logging

from opencensus.trace import attributes_helper
from opencensus.trace import tracer as tracer_module
from opencensus.trace.ext import grpc as oc_grpc
from opencensus.trace.propagation import binary_format

ATTRIBUTE_COMPONENT = 'COMPONENT'
ATTRIBUTE_ERROR_NAME = 'ERROR_NAME'
ATTRIBUTE_ERROR_MESSAGE = 'ERROR_MESSAGE'


class OpenCensusServerInterceptor(grpc.ServerInterceptor):

    def __init__(self, sampler=None, exporter=None):
        self.sampler = sampler
        self.exporter = exporter

    def _start_server_span(self, tracer):
        span = tracer.start_span(name='grpc_server')
        tracer.add_attribute_to_current_span(
            attribute_key=attributes_helper.COMMON_ATTRIBUTES.get(
                ATTRIBUTE_COMPONENT),
            attribute_value='grpc')

        return span

    def intercept_handler(self, continuation, handler_call_details):
        metadata = handler_call_details.invocation_metadata
        span_context = None

        if metadata is not None:
            propagator = binary_format.BinaryFormatPropagator()
            metadata_dict = dict(metadata)
            trace_header = metadata_dict.get(oc_grpc.GRPC_TRACE_KEY)

            span_context = propagator.from_header(trace_header)

        tracer = tracer_module.Tracer(span_context=span_context,
                                      sampler=self.sampler,
                                      exporter=self.exporter)

        with self._start_server_span(tracer):
            response = None

            try:
                response = continuation(handler_call_details)
            except Exception as e:  # pragma: NO COVER
                logging.error(e)
                tracer.add_attribute_to_current_span(
                    attributes_helper.COMMON_ATTRIBUTES.get(
                        ATTRIBUTE_ERROR_MESSAGE),
                    str(e))
                tracer.end_span()
                raise

        return response

    def intercept_service(self, continuation, handler_call_details):
        return self.intercept_handler(continuation, handler_call_details)
