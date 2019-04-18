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
from opencensus.trace import span as span_module
from opencensus.trace import tracer as tracer_module
from opencensus.trace import utils
from opencensus.trace.propagation import trace_context_http_header_format
from opencensus.trace.samplers import always_on

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:  # pragma: NO COVER
    MiddlewareMixin = object

HTTP_METHOD = attributes_helper.COMMON_ATTRIBUTES['HTTP_METHOD']
HTTP_URL = attributes_helper.COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = attributes_helper.COMMON_ATTRIBUTES['HTTP_STATUS_CODE']

REQUEST_THREAD_LOCAL_KEY = 'django_request'
SPAN_THREAD_LOCAL_KEY = 'django_span'

BLACKLIST_PATHS = 'BLACKLIST_PATHS'
BLACKLIST_HOSTNAMES = 'BLACKLIST_HOSTNAMES'

log = logging.getLogger(__name__)


class _DjangoMetaWrapper(object):
    """
    Wrapper class which takes HTTP header name and retrieve the value from
    Django request.META
    """

    def __init__(self, meta=None):
        self.meta = meta or _get_django_request().META

    def get(self, key):
        return self.meta.get('HTTP_' + key.upper().replace('-', '_'))


def _get_django_request():
    """Get Django request from thread local.

    :rtype: str
    :returns: Django request.
    """
    return execution_context.get_opencensus_attr(REQUEST_THREAD_LOCAL_KEY)


def _get_django_span():
    """Get Django span from thread local.

    :rtype: str
    :returns: Django request.
    """
    return execution_context.get_opencensus_attr(SPAN_THREAD_LOCAL_KEY)


def _get_current_tracer():
    """Get the current request tracer."""
    return execution_context.get_opencensus_tracer()


def _set_django_attributes(span, request):
    """Set the django related attributes."""
    django_user = getattr(request, 'user', None)

    if django_user is None:
        return

    user_id = django_user.pk
    try:
        user_name = django_user.get_username()
    except AttributeError:
        # AnonymousUser in some older versions of Django doesn't implement
        # get_username
        return

    # User id is the django autofield for User model as the primary key
    if user_id is not None:
        span.add_attribute('django.user.id', str(user_id))

    if user_name is not None:
        span.add_attribute('django.user.name', str(user_name))


class OpencensusMiddleware(MiddlewareMixin):
    """Saves the request in thread local"""

    def __init__(self, get_response=None):
        self.get_response = get_response
        settings = getattr(django.conf.settings, 'OPENCENSUS', {})
        settings = settings.get('TRACE', {})

        self.sampler = settings.get('SAMPLER', None) or \
            always_on.AlwaysOnSampler()
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

    def process_request(self, request):
        """Called on each request, before Django decides which view to execute.

        :type request: :class:`~django.http.request.HttpRequest`
        :param request: Django http request.
        """
        # Do not trace if the url is blacklisted
        if utils.disable_tracing_url(request.path, self.blacklist_paths):
            return

        # Add the request to thread local
        execution_context.set_opencensus_attr(
            REQUEST_THREAD_LOCAL_KEY,
            request)

        execution_context.set_opencensus_attr(
            'blacklist_hostnames',
            self.blacklist_hostnames)

        try:
            # Start tracing this request
            span_context = self.propagator.from_headers(
                _DjangoMetaWrapper(_get_django_request().META))

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
                attribute_value=str(request.path))

            # Add the span to thread local
            # in some cases (exceptions, timeouts) currentspan in
            # response event will be one of a child spans.
            # let's keep reference to 'django' span and
            # use it in response event
            execution_context.set_opencensus_attr(
                SPAN_THREAD_LOCAL_KEY,
                span)

        except Exception:  # pragma: NO COVER
            log.error('Failed to trace request', exc_info=True)

    def process_view(self, request, view_func, *args, **kwargs):
        """Process view is executed before the view function, here we get the
        function name add set it as the span name.
        """

        # Do not trace if the url is blacklisted
        if utils.disable_tracing_url(request.path, self.blacklist_paths):
            return

        try:
            # Get the current span and set the span name to the current
            # function name of the request.
            tracer = _get_current_tracer()
            span = tracer.current_span()
            span.name = utils.get_func_name(view_func)
        except Exception:  # pragma: NO COVER
            log.error('Failed to trace request', exc_info=True)

    def process_response(self, request, response):
        # Do not trace if the url is blacklisted
        if utils.disable_tracing_url(request.path, self.blacklist_paths):
            return response

        try:
            span = _get_django_span()
            span.add_attribute(
                attribute_key=HTTP_STATUS_CODE,
                attribute_value=str(response.status_code))

            _set_django_attributes(span, request)

            tracer = _get_current_tracer()
            tracer.end_span()
            tracer.finish()
        except Exception:  # pragma: NO COVER
            log.error('Failed to trace request', exc_info=True)
        finally:
            return response
