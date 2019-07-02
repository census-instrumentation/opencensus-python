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

"""Django middleware helper to capture and trace a request."""
import logging
import six

import django.conf

from opencensus.common import configuration
from opencensus.trace import attributes_helper
from opencensus.trace import execution_context
from opencensus.trace import print_exporter
from opencensus.trace import samplers
from opencensus.trace import span as span_module
from opencensus.trace import tracer as tracer_module
from opencensus.trace import utils
from opencensus.trace.propagation import trace_context_http_header_format

HTTP_METHOD = attributes_helper.COMMON_ATTRIBUTES['HTTP_METHOD']
HTTP_URL = attributes_helper.COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = attributes_helper.COMMON_ATTRIBUTES['HTTP_STATUS_CODE']

BLACKLIST_PATHS = 'BLACKLIST_PATHS'
BLACKLIST_HOSTNAMES = 'BLACKLIST_HOSTNAMES'

log = logging.getLogger(__name__)


class _DjangoMetaWrapper(object):
    """
    Wrapper class which takes HTTP header name and retrieve the value from
    Django request.META
    """

    def __init__(self, meta):
        self.meta = meta

    def get(self, key):
        return self.meta.get('HTTP_' + key.upper().replace('-', '_'))


class OpencensusMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

        settings = getattr(django.conf.settings, 'OPENCENSUS', {})
        settings = settings.get('TRACE', {})

        self.sampler = (settings.get('SAMPLER', None)
                        or samplers.ProbabilitySampler())
        if isinstance(self.sampler, six.string_types):
            self.sampler = configuration.load(self.sampler)

        self.exporter = settings.get('EXPORTER', None) or \
            print_exporter.PrintExporter()
        if isinstance(self.exporter, six.string_types):
            self.exporter = configuration.load(self.exporter)

        self.propagator = settings.get('PROPAGATOR', None) or \
            trace_context_http_header_format.TraceContextPropagator()
        if isinstance(self.propagator, six.string_types):
            self.propagator = configuration.load(self.propagator)

        self.blacklist_paths = settings.get(BLACKLIST_PATHS, None)

        self.blacklist_hostnames = settings.get(BLACKLIST_HOSTNAMES, None)

    def __call__(self, request):
        """
        :type request: :class:`~django.http.request.HttpRequest`
        :param request: Django http request.
        """
        span = None

        # Do not trace if the url is blacklisted
        if not utils.disable_tracing_url(request.path, self.blacklist_paths):
            # Add the request to thread local
            execution_context.set_opencensus_attr(
                'blacklist_hostnames',
                self.blacklist_hostnames)

            try:
                # Start tracing this request
                span_context = self.propagator.from_headers(
                    _DjangoMetaWrapper(request.META))

                # Reload the tracer with the new span context
                tracer = tracer_module.Tracer(
                    span_context=span_context,
                    sampler=self.sampler,
                    exporter=self.exporter,
                    propagator=self.propagator)

                # Span name is being set at process_view
                span = tracer.start_span()
                span.span_kind = span_module.SpanKind.SERVER
                tracer.add_attribute_to_current_span(
                    attribute_key=HTTP_METHOD,
                    attribute_value=request.method)
                tracer.add_attribute_to_current_span(
                    attribute_key=HTTP_URL,
                    attribute_value=request.path)

            except Exception:  # pragma: NO COVER
                log.error('Failed to trace request', exc_info=True)


        response = self.get_response(request)

        if span:
            try:
                span.name = utils.get_func_name(request.resolver_match.func)

                span.add_attribute(
                    attribute_key=HTTP_STATUS_CODE,
                    attribute_value=str(response.status_code))

                self.set_django_attributes(span, request, response)

                tracer.end_span()
                tracer.finish()
            except Exception:  # pragma: NO COVER
                log.error('Failed to trace request', exc_info=True)

        return response

    def set_django_attributes(self, span, request, response):  # pragma: NO COVER
        """ The last method before the span finishes, allowing to set
            django-related attributes on the span. Override this in a
            subclass of the middleware to set custom attributes.
        """
        django_user = getattr(request, 'user', None)

        if django_user is None:
            return

        user_id = django_user.pk
        user_name = django_user.get_username()

        # User id is the django autofield for User model as the primary key
        if user_id is not None:
            span.add_attribute('django.user.id', str(user_id))

        if user_name is not None:
            span.add_attribute('django.user.name', str(user_name))
