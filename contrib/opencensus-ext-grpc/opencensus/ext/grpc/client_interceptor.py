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

from opencensus.ext import grpc as oc_grpc
from opencensus.ext.grpc import utils as grpc_utils
from opencensus.trace import attributes_helper
from opencensus.trace import execution_context
from opencensus.trace import span as span_module
from opencensus.trace import time_event
from opencensus.trace.propagation import binary_format

log = logging.getLogger(__name__)

ATTRIBUTE_COMPONENT = 'COMPONENT'
ATTRIBUTE_ERROR_NAME = 'ERROR_NAME'
ATTRIBUTE_ERROR_MESSAGE = 'ERROR_MESSAGE'
GRPC_HOST_PORT = 'GRPC_HOST_PORT'
GRPC_METHOD = 'GRPC_METHOD'
SENT_PREFIX = 'Sent'

TIMEOUT = 3

# Do not trace StackDriver Trace exporter activities to avoid deadlock.
CLOUD_TRACE = 'google.devtools.cloudtrace'


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
        self._tracer = tracer
        self.host_port = host_port
        self._propagator = binary_format.BinaryFormatPropagator()

    @property
    def tracer(self):
        return self._tracer or execution_context.get_opencensus_tracer()

    def _start_client_span(self, client_call_details):
        span = self.tracer.start_span(
            name=_get_span_name(client_call_details)
        )

        span.span_kind = span_module.SpanKind.CLIENT
        # Add the component grpc to span attribute
        self.tracer.add_attribute_to_current_span(
            attribute_key=attributes_helper.COMMON_ATTRIBUTES.get(
                ATTRIBUTE_COMPONENT),
            attribute_value='grpc')

        # Add the host:port info to span attribute
        self.tracer.add_attribute_to_current_span(
            attribute_key=attributes_helper.GRPC_ATTRIBUTES.get(
                GRPC_HOST_PORT),
            attribute_value=self.host_port)

        # Add the method to span attribute
        self.tracer.add_attribute_to_current_span(
            attribute_key=attributes_helper.GRPC_ATTRIBUTES.get(GRPC_METHOD),
            attribute_value=str(client_call_details.method))

        return span

    def _intercept_call(
        self, client_call_details, request_iterator, grpc_type
    ):
        metadata = ()
        if client_call_details.metadata is not None:
            metadata = client_call_details.metadata

        # Start a span
        current_span = self._start_client_span(client_call_details)

        span_context = current_span.context_tracer.span_context
        header = self._propagator.to_header(span_context)
        grpc_trace_metadata = {
            oc_grpc.GRPC_TRACE_KEY: header,
        }

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

        request_iterator = grpc_utils.wrap_iter_with_message_events(
            request_or_response_iter=request_iterator,
            span=current_span,
            message_event_type=time_event.Type.SENT
        )

        return client_call_details, request_iterator, current_span

    def _callback(self, current_span):
        def callback(future_response):
            grpc_utils.add_message_event(
                proto_message=future_response.result(),
                span=current_span,
                message_event_type=time_event.Type.RECEIVED,
            )
            self._trace_future_exception(future_response)
            self.tracer.end_span()

        return callback

    def _trace_future_exception(self, response):
        # Trace the exception for a grpc.Future if any
        exception = response.exception()

        if exception is not None:
            exception = str(exception)

        self.tracer.add_attribute_to_current_span(
            attribute_key=attributes_helper.COMMON_ATTRIBUTES.get(
                ATTRIBUTE_ERROR_MESSAGE),
            attribute_value=exception)

    def intercept_unary_unary(
        self, continuation, client_call_details, request
    ):
        if CLOUD_TRACE in client_call_details.method:
            response = continuation(client_call_details, request)
            return response

        new_details, new_request, current_span = self._intercept_call(
            client_call_details=client_call_details,
            request_iterator=iter((request,)),
            grpc_type=oc_grpc.UNARY_UNARY)

        response = continuation(
            new_details,
            next(new_request))

        response.add_done_callback(self._callback(current_span))

        return response

    def intercept_unary_stream(
        self, continuation, client_call_details, request
    ):
        if CLOUD_TRACE in client_call_details.method:
            response = continuation(client_call_details, request)
            return response

        new_details, new_request_iterator, current_span = self._intercept_call(
            client_call_details=client_call_details,
            request_iterator=iter((request,)),
            grpc_type=oc_grpc.UNARY_STREAM)

        return grpc_utils.WrappedResponseIterator(
            continuation(new_details, next(new_request_iterator)),
            current_span)

    def intercept_stream_unary(
        self, continuation, client_call_details, request_iterator
    ):
        if CLOUD_TRACE in client_call_details.method:
            response = continuation(client_call_details, request_iterator)
            return response

        new_details, new_request_iterator, current_span = self._intercept_call(
            client_call_details=client_call_details,
            request_iterator=request_iterator,
            grpc_type=oc_grpc.STREAM_UNARY)

        response = continuation(
            new_details,
            new_request_iterator)

        response.add_done_callback(self._callback(current_span))

        return response

    def intercept_stream_stream(
        self, continuation, client_call_details, request_iterator
    ):
        if CLOUD_TRACE in client_call_details.method:
            response = continuation(client_call_details, request_iterator)
            return response

        new_details, new_request_iterator, current_span = self._intercept_call(
            client_call_details=client_call_details,
            request_iterator=request_iterator,
            grpc_type=oc_grpc.STREAM_STREAM)

        return grpc_utils.WrappedResponseIterator(
            continuation(new_details, new_request_iterator), current_span)


def _get_span_name(client_call_details):
    """Generates a span name based off of the gRPC client call details"""
    method_name = client_call_details.method[1:].replace('/', '.')
    return '{}.{}'.format(SENT_PREFIX, method_name)
