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

from opencensus.ext.django.config import (settings, convert_to_import)
from opencensus.trace import attributes_helper
from opencensus.trace import execution_context
from opencensus.trace import span as span_module
from opencensus.trace import tracer as tracer_module
from opencensus.trace import utils
from opencensus.trace.samplers import probability

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
GCP_EXPORTER_PROJECT = 'GCP_EXPORTER_PROJECT'
SAMPLING_RATE = 'SAMPLING_RATE'
TRANSPORT = 'TRANSPORT'
SERVICE_NAME = 'SERVICE_NAME'
ZIPKIN_EXPORTER_SERVICE_NAME = 'ZIPKIN_EXPORTER_SERVICE_NAME'
ZIPKIN_EXPORTER_HOST_NAME = 'ZIPKIN_EXPORTER_HOST_NAME'
ZIPKIN_EXPORTER_PORT = 'ZIPKIN_EXPORTER_PORT'
ZIPKIN_EXPORTER_PROTOCOL = 'ZIPKIN_EXPORTER_PROTOCOL'
JAEGER_EXPORTER_HOST_NAME = 'JAEGER_EXPORTER_HOST_NAME'
JAEGER_EXPORTER_PORT = 'JAEGER_EXPORTER_PORT'
JAEGER_EXPORTER_AGENT_HOST_NAME = 'JAEGER_EXPORTER_AGENT_HOST_NAME'
JAEGER_EXPORTER_AGENT_PORT = 'JAEGER_EXPORTER_AGENT_PORT'
JAEGER_EXPORTER_SERVICE_NAME = 'JAEGER_EXPORTER_SERVICE_NAME'
OCAGENT_TRACE_EXPORTER_ENDPOINT = 'OCAGENT_TRACE_EXPORTER_ENDPOINT'
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
    user_name = django_user.get_username()

    # User id is the django autofield for User model as the primary key
    if user_id is not None:
        span.add_attribute('django.user.id', str(user_id))

    if user_name is not None:
        span.add_attribute('django.user.name', str(user_name))


class OpencensusMiddleware(MiddlewareMixin):
    """Saves the request in thread local"""

    def __init__(self, get_response=None):
        # One-time configuration and initialization.
        self.get_response = get_response
        self._sampler = settings.SAMPLER
        self._exporter = settings.EXPORTER
        self._propagator = settings.PROPAGATOR

        self._blacklist_paths = settings.params.get(BLACKLIST_PATHS)

        # Initialize the sampler
        if self._sampler.__name__ == 'ProbabilitySampler':
            _rate = settings.params.get(
                SAMPLING_RATE, probability.DEFAULT_SAMPLING_RATE)
            self.sampler = self._sampler(_rate)
        else:
            self.sampler = self._sampler()

        # Initialize the exporter
        transport = convert_to_import(settings.params.get(TRANSPORT))

        if self._exporter.__name__ == 'GoogleCloudExporter':
            _project_id = settings.params.get(GCP_EXPORTER_PROJECT, None)
            self.exporter = self._exporter(
                project_id=_project_id,
                transport=transport)
        elif self._exporter.__name__ == 'ZipkinExporter':
            _service_name = self._get_service_name(settings.params)
            _zipkin_host_name = settings.params.get(
                ZIPKIN_EXPORTER_HOST_NAME, 'localhost')
            _zipkin_port = settings.params.get(
                ZIPKIN_EXPORTER_PORT, 9411)
            _zipkin_protocol = settings.params.get(
                ZIPKIN_EXPORTER_PROTOCOL, 'http')
            self.exporter = self._exporter(
                service_name=_service_name,
                host_name=_zipkin_host_name,
                port=_zipkin_port,
                protocol=_zipkin_protocol,
                transport=transport)
        elif self._exporter.__name__ == 'TraceExporter':
            _service_name = self._get_service_name(settings.params)
            _endpoint = settings.params.get(
                OCAGENT_TRACE_EXPORTER_ENDPOINT, None)
            self.exporter = self._exporter(
                service_name=_service_name,
                endpoint=_endpoint,
                transport=transport)
        elif self._exporter.__name__ == 'JaegerExporter':
            _service_name = settings.params.get(
                JAEGER_EXPORTER_SERVICE_NAME,
                self._get_service_name(settings.params))
            _jaeger_host_name = settings.params.get(
                JAEGER_EXPORTER_HOST_NAME, None)
            _jaeger_port = settings.params.get(
                JAEGER_EXPORTER_PORT, None)
            _jaeger_agent_host_name = settings.params.get(
                JAEGER_EXPORTER_AGENT_HOST_NAME, 'localhost')
            _jaeger_agent_port = settings.params.get(
                JAEGER_EXPORTER_AGENT_PORT, 6831)
            self.exporter = self._exporter(
                service_name=_service_name,
                host_name=_jaeger_host_name,
                port=_jaeger_port,
                agent_host_name=_jaeger_agent_host_name,
                agent_port=_jaeger_agent_port,
                transport=transport)
        else:
            self.exporter = self._exporter(transport=transport)

        self.blacklist_hostnames = settings.params.get(
            BLACKLIST_HOSTNAMES, None)

        # Initialize the propagator
        self.propagator = self._propagator()

    def process_request(self, request):
        """Called on each request, before Django decides which view to execute.

        :type request: :class:`~django.http.request.HttpRequest`
        :param request: Django http request.
        """
        # Do not trace if the url is blacklisted
        if utils.disable_tracing_url(request.path, self._blacklist_paths):
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
        if utils.disable_tracing_url(request.path, self._blacklist_paths):
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
        if utils.disable_tracing_url(request.path, self._blacklist_paths):
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

    def _get_service_name(self, params):
        _service_name = params.get(
            SERVICE_NAME, None)

        if _service_name is None:
            _service_name = params.get(
                ZIPKIN_EXPORTER_SERVICE_NAME, 'my_service')

        return _service_name
