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

import inspect
import logging

import grpc

from google.cloud import _helpers

from opencensus.trace import execution_context
from opencensus.trace.grpc.client_interceptor import (
    OpenCensusClientInterceptor)
from opencensus.trace.grpc.grpc_ext import intercept_channel

from opencensus.trace.ext.requests.trace import (
    trace_integration as trace_requests)


log = logging.getLogger(__name__)

MODULE_NAME = 'cloud_clientlibs'

MAKE_SECURE_CHANNEL = 'make_secure_channel'
INSECURE_CHANNEL = 'insecure_channel'


def trace_integration():
    """Wrap the mysql connector to trace it."""
    log.info('Integrated module: {}'.format(MODULE_NAME))

    # Integrate with gRPC
    trace_grpc()

    # Integrate with HTTP
    trace_http()


def trace_grpc():
    """Integrate with gRPC."""
    # Wrap google.cloud._helpers.make_secure_channel
    make_secure_channel_func = getattr(_helpers, MAKE_SECURE_CHANNEL)
    make_secure_channel_module = inspect.getmodule(make_secure_channel_func)
    make_secure_channel_wrapped = wrap_make_secure_channel(
        make_secure_channel_func)
    setattr(
        make_secure_channel_module,
        MAKE_SECURE_CHANNEL,
        make_secure_channel_wrapped)

    # Wrap the grpc.insecure_channel.
    insecure_channel_func = getattr(grpc, INSECURE_CHANNEL)
    insecure_channel_module = inspect.getmodule(insecure_channel_func)
    insecure_channel_wrapped = wrap_insecure_channel(
        insecure_channel_func)
    setattr(
        insecure_channel_module,
        INSECURE_CHANNEL,
        insecure_channel_wrapped)


def trace_http():
    """Integrate with HTTP (requests library)."""
    trace_requests()


def wrap_make_secure_channel(make_secure_channel_func):
    """Wrap the google.cloud._helpers.make_secure_channel."""
    def call(*args, **kwargs):
        channel = make_secure_channel_func(*args, **kwargs)

        try:
            host = kwargs.get('host')
            _tracer = execution_context.get_opencensus_tracer()
            tracer_interceptor = OpenCensusClientInterceptor(_tracer, host)
            intercepted_channel = intercept_channel(
                channel, tracer_interceptor)
            return intercepted_channel
        except Exception:
            log.warning(
                'Failed to wrap secure channel, '
                'clientlibs grpc calls not traced.')
            return channel
    return call


def wrap_insecure_channel(insecure_channel_func):
    """Wrap the grpc.insecure_channel."""
    def call(*args, **kwargs):
        channel = insecure_channel_func(*args, **kwargs)

        try:
            target = kwargs.get('target')
            _tracer = execution_context.get_opencensus_tracer()
            tracer_interceptor = OpenCensusClientInterceptor(_tracer, target)
            intercepted_channel = intercept_channel(
                channel, tracer_interceptor)
            return intercepted_channel
        except Exception:
            log.warning(
                'Failed to wrap insecure channel, '
                'clientlibs grpc calls not traced.')
            return channel
    return call
