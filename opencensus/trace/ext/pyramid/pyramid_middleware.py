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

from opencensus.trace.ext import utils
from opencensus.trace.ext.pyramid.config import PyramidTraceSettings

from opencensus.trace import attributes_helper
from opencensus.trace import execution_context
from opencensus.trace import tracer as tracer_module


HTTP_METHOD = attributes_helper.COMMON_ATTRIBUTES['HTTP_METHOD']
HTTP_URL = attributes_helper.COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = attributes_helper.COMMON_ATTRIBUTES['HTTP_STATUS_CODE']

_PYRAMID_TRACE_HEADER = 'X_CLOUD_TRACE_CONTEXT'

BLACKLIST_PATHS = 'BLACKLIST_PATHS'


log = logging.getLogger(__name__)


class OpenCensusTweenFactory(object):
    """Pyramid tweens are like wsgi middleware, but have access to things
    like the request, response, and application registry.

    The tween factory is a globally importable callable whose
    constructor takes a request handler and application registry. It
    will be called with a pyramid request object.

    For details on pyramid tweens, see
    https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hooks.html#creating-a-tween
    """
    def __init__(self, handler, registry):
        """Constructor for the pyramid tween

        :param handler: Either the main Pyramid request handling
        function or another tween
        :type handler: function
        :param registry: The pyramid application registry
        :type registry: :class:`pyramid.registry.Registry`
        """
        self.handler = handler
        self.registry = registry
        settings = PyramidTraceSettings(registry)

        self.sampler = settings.SAMPLER
        self.exporter = settings.EXPORTER
        self.propagator = settings.PROPAGATOR

        self._blacklist_paths = settings.params.get(BLACKLIST_PATHS)

    def __call__(self, request):
        self._before_request(request)

        response = self.handler(request)

        self._after_request(request, response)

        return response

    def _before_request(self, request):
        if utils.disable_tracing_url(request.path, self._blacklist_paths):
            return

        try:
            header = get_context_header(request)
            span_context = self.propagator.from_header(header)

            tracer = tracer_module.Tracer(
                span_context=span_context,
                sampler=self.sampler,
                exporter=self.exporter,
                propagator=self.propagator)

            span = tracer.start_span()

            # Set the span name as the name of the current module name
            span.name = '[{}]{}'.format(
                request.method,
                request.path)

            tracer.add_attribute_to_current_span(
                attribute_key=HTTP_METHOD,
                attribute_value=request.method)
            tracer.add_attribute_to_current_span(
                attribute_key=HTTP_URL,
                attribute_value=request.path)
        except Exception:  # pragma: NO COVER
            log.error('Failed to trace request', exc_info=True)

    def _after_request(self, request, response):
        if utils.disable_tracing_url(request.path, self._blacklist_paths):
            return

        try:
            tracer = execution_context.get_opencensus_tracer()
            tracer.add_attribute_to_current_span(
                HTTP_STATUS_CODE,
                str(response.status_code))

            tracer.end_span()
            tracer.finish()
        except Exception:  # pragma: NO COVER
            log.error('Failed to trace request', exc_info=True)


def get_context_header(request):
    """Get trace context header from pyramid request headers."""
    return request.headers.get(_PYRAMID_TRACE_HEADER)
