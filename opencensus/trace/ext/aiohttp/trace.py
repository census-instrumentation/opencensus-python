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
import aiohttp

from opencensus.trace import asyncio_context

log = logging.getLogger(__name__)

MODULE_NAME = 'aiohttp'


def trace_integration(tracer=None, propagator=None):
    """Wrap the requests library to trace it."""
    log.info('Integrated module: {}'.format(MODULE_NAME))
    # Wrap the aiohttp functions
    aiohttp_func = getattr(aiohttp.ClientSession, '__init__')
    wrapped = wrap_aiohttp(aiohttp_func)
    setattr(aiohttp.ClientSession, aiohttp_func.__name__, wrapped)


def wrap_aiohttp(aiohttp_func):
    """Wrap the aiohttp function to trace it."""
    def call(*args, **kwargs):
        async def on_request_start(session, context, params):
            _tracer = asyncio_context.get_opencensus_tracer()
            _span = _tracer.start_span()
            _span.name = '[aiohttp]{}'.format(params.method)
            _tracer.add_attribute_to_current_span('aiohttp/url', params.url)
            return

        async def on_request_end(session, context, params):
            _tracer = asyncio_context.get_opencensus_tracer()
            _tracer.add_attribute_to_current_span(
                'aiohttp/status_code', str(params.response.status))
            _tracer.end_span()
            return

        trace_config = aiohttp.TraceConfig()
        trace_config.on_request_start.append(on_request_start)
        trace_config.on_request_end.append(on_request_end)
        kwargs['trace_configs'] = [trace_config]

        return aiohttp_func(*args, **kwargs)

    return call
