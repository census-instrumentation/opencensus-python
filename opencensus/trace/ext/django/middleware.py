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

from opencensus.trace.ext import utils
from opencensus.trace.ext.django.config import (settings, convert_to_import)
from opencensus.trace import attributes_helper
from opencensus.trace import tracer as tracer_module
from opencensus.trace import execution_context
from opencensus.trace.samplers import probability

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:  # pragma: NO COVER
    MiddlewareMixin = object

HTTP_METHOD = attributes_helper.COMMON_ATTRIBUTES['HTTP_METHOD']
HTTP_URL = attributes_helper.COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = attributes_helper.COMMON_ATTRIBUTES['HTTP_STATUS_CODE']

REQUEST_THREAD_LOCAL_KEY = 'django_request'

_DJANGO_TRACE_HEADER = 'HTTP_X_CLOUD_TRACE_CONTEXT'

BLACKLIST_PATHS = 'BLACKLIST_PATHS'
GCP_EXPORTER_PROJECT = 'GCP_EXPORTER_PROJECT'
SAMPLING_RATE = 'SAMPLING_RATE'
TRANSPORT = 'TRANSPORT'
ZIPKIN_EXPORTER_SERVICE_NAME = 'ZIPKIN_EXPORTER_SERVICE_NAME'
ZIPKIN_EXPORTER_HOST_NAME = 'ZIPKIN_EXPORTER_HOST_NAME'
ZIPKIN_EXPORTER_PORT = 'ZIPKIN_EXPORTER_PORT'


log = logging.getLogger(__name__)


def _get_django_request():
    """Get Django request from thread local.

    :rtype: str
    :returns: Django request.
    """
    return execution_context.get_opencensus_attr(REQUEST_THREAD_LOCAL_KEY)


def _get_current_tracer():
    """Get the current request tracer."""
    return execution_context.get_opencensus_tracer()


def _set_django_attributes(tracer, request):
    """Set the django related attributes."""
    django_user = getattr(request, 'user', None)

    if django_user is None:
        return

    user_id = django_user.pk
    user_name = django_user.get_username()

    # User id is the django autofield for User model as the primary key
    if user_id is not None:
        tracer.add_attribute_to_current_span('/django/user/id', str(user_id))

    if user_name is not None:
        tracer.add_attribute_to_current_span('/django/user/name', user_name)


def get_django_header():
    """Get trace context header from django request headers.

    :rtype: str
    :returns: Trace context header in HTTP request headers.
    """
    request = _get_django_request()

    header = request.META.get(_DJANGO_TRACE_HEADER)

    return header


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
            _zipkin_service_name = settings.params.get(
                ZIPKIN_EXPORTER_SERVICE_NAME, 'my_service')
            _zipkin_host_name = settings.params.get(
                ZIPKIN_EXPORTER_HOST_NAME, 'localhost')
            _zipkin_port = settings.params.get(
                ZIPKIN_EXPORTER_PORT, 9411)
            self.exporter = self._exporter(
                service_name=_zipkin_service_name,
                host_name=_zipkin_host_name,
                port=_zipkin_port,
                transport=transport)
        else:
            self.exporter = self._exporter(transport=transport)

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

        try:
            # Start tracing this request
            header = get_django_header()
            span_context = self.propagator.from_header(header)

            # Reload the tracer with the new span context
            tracer = tracer_module.Tracer(
                span_context=span_context,
                sampler=self.sampler,
                exporter=self.exporter,
                propagator=self.propagator)

            # Span name is being set at process_view
            tracer.start_span()
            tracer.add_attribute_to_current_span(
                attribute_key=HTTP_METHOD,
                attribute_value=request.method)
            tracer.add_attribute_to_current_span(
                attribute_key=HTTP_URL,
                attribute_value=request.path)
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
            tracer = _get_current_tracer()
            tracer.add_attribute_to_current_span(
                attribute_key=HTTP_STATUS_CODE,
                attribute_value=str(response.status_code))

            _set_django_attributes(tracer, request)

            tracer.end_span()
            tracer.finish()
        except Exception:  # pragma: NO COVER
            log.error('Failed to trace request', exc_info=True)
        finally:
            return response
