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

import logging

import grpc

from google.cloud import _helpers
from google.api_core import grpc_helpers

from opencensus.ext.grpc.client_interceptor import (
    OpenCensusClientInterceptor)

from opencensus.ext.requests.trace import (
    trace_integration as trace_requests)

log = logging.getLogger(__name__)

MODULE_NAME = 'google_cloud_clientlibs'

MAKE_SECURE_CHANNEL = 'make_secure_channel'
INSECURE_CHANNEL = 'insecure_channel'
CREATE_CHANNEL = 'create_channel'


def trace_integration(tracer=None):
    """Trace the Google Cloud Client libraries by integrating with
    the transport level including HTTP and gRPC.
    """
    log.info('Integrated module: {}'.format(MODULE_NAME))

    # Integrate with gRPC
    trace_grpc(tracer)

    # Integrate with HTTP
    trace_http(tracer)


def trace_grpc(tracer=None):
    """Integrate with gRPC."""
    # Wrap google.cloud._helpers.make_secure_channel
    make_secure_channel_func = getattr(_helpers, MAKE_SECURE_CHANNEL)
    make_secure_channel_wrapped = wrap_make_secure_channel(
        make_secure_channel_func, tracer)
    setattr(
        _helpers,
        MAKE_SECURE_CHANNEL,
        make_secure_channel_wrapped)

    # Wrap the grpc.insecure_channel.
    insecure_channel_func = getattr(grpc, INSECURE_CHANNEL)
    insecure_channel_wrapped = wrap_insecure_channel(
        insecure_channel_func, tracer)
    setattr(
        grpc,
        INSECURE_CHANNEL,
        insecure_channel_wrapped)

    # Wrap google.api_core.grpc_helpers.create_channel
    create_channel_func = getattr(grpc_helpers, CREATE_CHANNEL)
    create_channel_wrapped = wrap_create_channel(create_channel_func, tracer)
    setattr(
        grpc_helpers,
        CREATE_CHANNEL,
        create_channel_wrapped)


def trace_http(tracer=None):
    """Integrate with HTTP (requests library)."""
    trace_requests(tracer)


def wrap_make_secure_channel(make_secure_channel_func, tracer=None):
    """Wrap the google.cloud._helpers.make_secure_channel."""
    def call(*args, **kwargs):
        channel = make_secure_channel_func(*args, **kwargs)

        try:
            host = kwargs.get('host')
            tracer_interceptor = OpenCensusClientInterceptor(tracer, host)
            intercepted_channel = grpc.intercept_channel(
                channel, tracer_interceptor)
            return intercepted_channel  # pragma: NO COVER
        except Exception:
            log.warning(
                'Failed to wrap secure channel, '
                'clientlibs grpc calls not traced.')
            return channel
    return call


def wrap_insecure_channel(insecure_channel_func, tracer=None):
    """Wrap the grpc.insecure_channel."""
    def call(*args, **kwargs):
        channel = insecure_channel_func(*args, **kwargs)

        try:
            target = kwargs.get('target')
            tracer_interceptor = OpenCensusClientInterceptor(tracer, target)
            intercepted_channel = grpc.intercept_channel(
                channel, tracer_interceptor)
            return intercepted_channel  # pragma: NO COVER
        except Exception:
            log.warning(
                'Failed to wrap insecure channel, '
                'clientlibs grpc calls not traced.')
            return channel
    return call


def wrap_create_channel(create_channel_func, tracer=None):
    """Wrap the google.api_core.grpc_helpers.create_channel."""
    def call(*args, **kwargs):
        channel = create_channel_func(*args, **kwargs)

        try:
            target = kwargs.get('target')
            tracer_interceptor = OpenCensusClientInterceptor(tracer, target)
            intercepted_channel = grpc.intercept_channel(
                channel, tracer_interceptor)
            return intercepted_channel  # pragma: NO COVER
        except Exception:
            log.warning(
                'Failed to wrap create_channel, '
                'clientlibs grpc calls not traced.')
            return channel
    return call
