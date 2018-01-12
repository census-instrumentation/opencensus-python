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

TIMEOUT = 3


class _ClientCallDetails(
    collections.namedtuple(
        '_ClientCallDetails',
        ('method', 'timeout', 'metadata', 'credentials')),
        grpc.ClientCallDetails):
    pass


class OpenCensusClientInterceptor(grpc.UnaryUnaryClientInterceptor,
                                  grpc.UnaryStreamClientInterceptor,
                                  grpc.StreamUnaryClientInterceptor,
                                  grpc.StreamStreamClientInterceptor):

    def __init__(self, tracer=None, host_port=None):
        if tracer is None:
            tracer = execution_context.get_opencensus_tracer()

        self._tracer = tracer
        self.host_port = host_port
        self._propagator = binary_format.BinaryFormatPropagator()

    def _start_client_span(self, method, grpc_type):
        span = self._tracer.start_span(
            name='[gRPC_client][{}]{}'.format(grpc_type, str(method)))

        # Add the component grpc to span attribute
        self._tracer.add_attribute_to_current_span(
            attribute_key=attributes_helper.COMMON_ATTRIBUTES.get(
                ATTRIBUTE_COMPONENT),
            attribute_value='grpc')

        # Add the host:port info to span attribute
        self._tracer.add_attribute_to_current_span(
            attribute_key=attributes_helper.GRPC_ATTRIBUTES.get(
                GRPC_HOST_PORT),
            attribute_value=self.host_port)

        # Add the method to span attribute
        self._tracer.add_attribute_to_current_span(
            attribute_key=attributes_helper.GRPC_ATTRIBUTES.get(GRPC_METHOD),
            attribute_value=str(method))

        return span

    def _end_span_between_context(self, current_span):
        execution_context.set_current_span(current_span)
        self._tracer.end_span()

    def _intercept_call(
            self, client_call_details, request_iterator, grpc_type):
        metadata = ()
        if client_call_details.metadata is not None:
            metadata = client_call_details.metadata

        # Start a span
        current_span = self._start_client_span(
            client_call_details.method,
            grpc_type)

        span_context = self._tracer.span_context
        header = self._propagator.to_header(span_context)
        grpc_trace_metadata = {
            oc_grpc.GRPC_TRACE_KEY: header,
        }

        metadata_to_append = None

        if isinstance(metadata, list):
            metadata_to_append = list(six.iteritems(grpc_trace_metadata))
        else:
            metadata_to_append = tuple(six.iteritems(grpc_trace_metadata))

        metadata = metadata + metadata_to_append

        client_call_details = _ClientCallDetails(
            client_call_details.method,
            client_call_details.timeout,
            metadata,
            client_call_details.credentials)

        return client_call_details, request_iterator, current_span

    def _callback(self, current_span):
        def callback(future_response):
            execution_context.set_current_span(current_span)
            self._trace_future_exception(future_response)
            self._tracer.end_span()

        return callback

    def _trace_future_exception(self, response):
        # Trace the exception for a grpc.Future if any
        exception = response.exception(timeout=TIMEOUT)

        if exception is not None:
            exception = str(exception)

        self._tracer.add_attribute_to_current_span(
            attribute_key=attributes_helper.COMMON_ATTRIBUTES.get(
                ATTRIBUTE_ERROR_MESSAGE),
            attribute_value=exception)

    def intercept_unary_unary(
            self, continuation, client_call_details, request):
        new_details, new_request, current_span = self._intercept_call(
            client_call_details=client_call_details,
            request_iterator=iter((request,)),
            grpc_type=oc_grpc.UNARY_UNARY)

        response = continuation(
            new_details,
            next(new_request))

        response.add_done_callback(self._callback(current_span))

        return response

    def intercept_unary_stream(self, continuation, client_call_details,
                               request):
        new_details, new_request_iterator, current_span = self._intercept_call(
            client_call_details=client_call_details,
            request_iterator=iter((request,)),
            grpc_type=oc_grpc.UNARY_STREAM)

        response_it = continuation(
            new_details,
            next(new_request_iterator))
        self._end_span_between_context(current_span)

        return response_it

    def intercept_stream_unary(self, continuation, client_call_details,
                               request_iterator):
        new_details, new_request_iterator, current_span = self._intercept_call(
            client_call_details=client_call_details,
            request_iterator=request_iterator,
            grpc_type=oc_grpc.STREAM_UNARY)

        response = continuation(
            new_details,
            new_request_iterator)

        response.add_done_callback(self._callback(current_span))

        return response

    def intercept_stream_stream(self, continuation, client_call_details,
                                request_iterator):
        new_details, new_request_iterator, current_span = self._intercept_call(
            client_call_details=client_call_details,
            request_iterator=request_iterator,
            grpc_type=oc_grpc.STREAM_STREAM)

        response_it = continuation(
            new_details,
            new_request_iterator)
        self._end_span_between_context(current_span)

        return response_it
