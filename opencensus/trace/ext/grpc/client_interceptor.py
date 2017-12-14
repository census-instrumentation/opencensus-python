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
import six
import sys

from opencensus.trace import execution_context
from opencensus.trace import attributes_helper
from opencensus.trace.ext import grpc as oc_grpc
from opencensus.trace.propagation import binary_format

log = logging.getLogger(__name__)

ATTRIBUTE_COMPONENT = 'COMPONENT'
ATTRIBUTE_ERROR_NAME = 'ERROR_NAME'
ATTRIBUTE_ERROR_MESSAGE = 'ERROR_MESSAGE'
GRPC_HOST_PORT = 'GRPC_HOST_PORT'
GRPC_METHOD = 'GRPC_METHOD'


class _ClientCallDetails(
        collections.namedtuple('_ClientCallDetails',
                               ('method', 'timeout', 'metadata',
                                'credentials')), grpc.ClientCallDetails):
    pass


class OpenCensusClientInterceptor(grpc.UnaryUnaryClientInterceptor,
                                  grpc.UnaryStreamClientInterceptor,
                                  grpc.StreamUnaryClientInterceptor,
                                  grpc.StreamStreamClientInterceptor):

    def __init__(self, tracer=None, host_port=None):
        if tracer is None:
            tracer = execution_context.get_opencensus_tracer()

        self._tracer = tracer
        self._current_span = None
        self.host_port = host_port
        self._propagator = binary_format.BinaryFormatPropagator()

    def _start_client_span(self, method):
        log.info('Start client span')
        span = self._tracer.start_span(
            name='[gRPC_client]{}'.format(str(method)))
        self._current_span = span

        # Add the component grpc to span attribute
        self._tracer.add_attribute_to_current_span(
            attribute_key=attributes_helper.COMMON_ATTRIBUTES.get(
                ATTRIBUTE_COMPONENT),
            attribute_value='grpc')

        # Add the host:port info to span attribute
        if self.host_port is not None:
            self._tracer.add_attribute_to_current_span(
                attribute_key=attributes_helper.GRPC_ATTRIBUTES.get(
                    GRPC_HOST_PORT),
                attribute_value=self.host_port)

        # Add the method to span attribute
        self._tracer.add_attribute_to_current_span(
            attribute_key=attributes_helper.GRPC_ATTRIBUTES.get(GRPC_METHOD),
            attribute_value=str(method))

        return span

    def _intercept_call(
            self, client_call_details, request_iterator, request_streaming,
            response_streaming):
        metadata = ()
        if client_call_details.metadata is not None:
            metadata = client_call_details.metadata

        # Start a span
        self._start_client_span(client_call_details.method)

        span_context = self._tracer.span_context
        header = self._propagator.to_header(span_context)
        grpc_trace_metadata = {
            oc_grpc.GRPC_TRACE_KEY: header,
        }
        metadata = metadata + tuple(six.iteritems(grpc_trace_metadata))

        client_call_details = _ClientCallDetails(
            client_call_details.method,
            client_call_details.timeout,
            metadata,
            client_call_details.credentials)

        return client_call_details, request_iterator

    def _end_span_between_context(self):
        execution_context.set_current_span(self._current_span)
        self._tracer.end_span()
        self._current_span = None

    def _future_done_callback(self):
        def callback(future_response):
            self._end_span_between_context()

        return callback

    def intercept_unary_unary(
            self, continuation, client_call_details, request):
        new_details, new_request = self._intercept_call(
            client_call_details, iter((request,)), False, False)

        response = continuation(new_details, next(new_request))

        if isinstance(response, grpc.Future):
            response.add_done_callback(self._future_done_callback())
        else:
            self._end_span_between_context()
        return response

    def intercept_unary_stream(self, continuation, client_call_details,
                               request):
        new_details, new_request_iterator = self._intercept_call(
            client_call_details, iter((request,)), False, True)
        response_it = continuation(new_details, next(new_request_iterator))
        self._end_span_between_context()
        return response_it

    def intercept_stream_unary(self, continuation, client_call_details,
                               request_iterator):
        new_details, new_request_iterator = self._intercept_call(
            client_call_details, iter((request_iterator,)), True, False)
        response = continuation(new_details, next(new_request_iterator))

        if isinstance(response, grpc.Future):
            response.add_done_callback(self._future_done_callback())
        else:
            self._end_span_between_context()
        return response

    def intercept_stream_stream(self, continuation, client_call_details,
                                request_iterator):
        new_details, new_request_iterator = self._intercept_call(
            client_call_details, request_iterator, True, True)
        response_it = continuation(new_details, new_request_iterator)
        self._end_span_between_context()
        return response_it
