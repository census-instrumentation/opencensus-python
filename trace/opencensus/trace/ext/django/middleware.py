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
from opencensus.trace.ext.django.config import settings
from opencensus.trace import labels_helper
from opencensus.trace import request_tracer
from opencensus.trace import execution_context
from opencensus.trace.samplers import fixed_rate

HTTP_METHOD = labels_helper.STACKDRIVER_LABELS['HTTP_METHOD']
HTTP_URL = labels_helper.STACKDRIVER_LABELS['HTTP_URL']
HTTP_STATUS_CODE = labels_helper.STACKDRIVER_LABELS['HTTP_STATUS_CODE']

REQUEST_THREAD_LOCAL_KEY = 'django_request'

_DJANGO_TRACE_HEADER = 'HTTP_X_CLOUD_TRACE_CONTEXT'

GCP_REPORTER_PROJECT = 'GCP_REPORTER_PROJECT'
SAMPLING_RATE = 'SAMPLING_RATE'
ZIPKIN_REPORTER_SERVICE_NAME = 'ZIPKIN_REPORTER_SERVICE_NAME'
ZIPKIN_REPORTER_HOST_NAME = 'ZIPKIN_REPORTER_HOST_NAME'
ZIPKIN_REPORTER_PORT = 'ZIPKIN_REPORTER_PORT'

log = logging.getLogger(__name__)


def _get_django_request():
    """Get Django request from thread local.

    :rtype: str
    :returns: Django request.
    """
    return execution_context.get_opencensus_attr(REQUEST_THREAD_LOCAL_KEY)


def _get_current_request_tracer():
    """Get the current request tracer."""
    return execution_context.get_opencensus_tracer()


def _set_django_labels(tracer, request):
    """Set the django related labels."""
    django_user = getattr(request, 'user', None)

    if django_user is None:
        return

    user_id = django_user.pk
    user_name = django_user.get_username()

    # User id is the django autofield for User model as the primary key
    if user_id is not None:
        tracer.add_label_to_spans('/django/user/id', str(user_id))

    if user_name is not None:
        tracer.add_label_to_spans('/django/user/name', user_name)


def get_django_header():
    """Get trace context header from django request headers.

    :rtype: str
    :returns: Trace context header in HTTP request headers.
    """
    request = _get_django_request()

    header = request.META.get(_DJANGO_TRACE_HEADER)

    return header


class OpencensusMiddleware(object):
    """Saves the request in thread local"""

    def __init__(self, get_response=None):
        # One-time configuration and initialization.
        self.get_response = get_response
        self._sampler = settings.SAMPLER
        self._reporter = settings.REPORTER
        self._propagator = settings.PROPAGATOR

        # Initialize the sampler
        if self._sampler.__name__ == 'FixedRateSampler':
            _rate = settings.params.get(
                SAMPLING_RATE, fixed_rate.DEFAULT_SAMPLING_RATE)
            self.sampler = self._sampler(_rate)
        else:
            self.sampler = self._sampler()

        # Initialize the reporter
        if self._reporter.__name__ == 'GoogleCloudReporter':
            _project_id = settings.params.get(GCP_REPORTER_PROJECT, None)
            self.reporter = self._reporter(project_id=_project_id)
        elif self._reporter.__name__ == 'ZipkinReporter':
            _zipkin_service_name = settings.params.get(
                ZIPKIN_REPORTER_SERVICE_NAME, 'my_service')
            _zipkin_host_name = settings.params.get(
                ZIPKIN_REPORTER_HOST_NAME, 'localhost')
            _zipkin_port = settings.params.get(
                ZIPKIN_REPORTER_PORT, 9411)
            self.reporter = self._reporter(
                service_name=_zipkin_service_name,
                host_name=_zipkin_host_name,
                port=_zipkin_port)
        else:
            self.reporter = self._reporter()

        # Initialize the propagator
        self.propagator = self._propagator()

    def process_request(self, request):
        """Called on each request, before Django decides which view to execute.

        :type request: :class:`~django.http.request.HttpRequest`
        :param request: Django http request.
        """
        # Add the request to thread local
        execution_context.set_opencensus_attr(
            REQUEST_THREAD_LOCAL_KEY,
            request)

        try:
            # Start tracing this request
            header = get_django_header()
            span_context = self.propagator.from_header(header)

            # Reload the tracer with the new span context
            tracer = request_tracer.RequestTracer(
                span_context=span_context,
                sampler=self.sampler,
                reporter=self.reporter,
                propagator=self.propagator)

            tracer.start_trace()

            # Span name is being set at process_view
            tracer.start_span()
            tracer.add_label_to_spans(
                label_key=HTTP_METHOD,
                label_value=request.method)
            tracer.add_label_to_spans(
                label_key=HTTP_URL,
                label_value=request.path)
        except Exception:  # pragma: NO COVER
            log.error('Failed to trace request', exc_info=True)

    def process_view(self, request, view_func, *args, **kwargs):
        """Process view is executed before the view function, here we get the
        function name add set it as the span name.
        """
        try:
            # Get the current span and set the span name to the current
            # function name of the request.
            tracer = _get_current_request_tracer()
            span = tracer.current_span()
            span.name = utils.get_func_name(view_func)
        except Exception:  # pragma: NO COVER
            log.error('Failed to trace request', exc_info=True)

    def process_response(self, request, response):
        try:
            tracer = _get_current_request_tracer()
            tracer.add_label_to_spans(
                label_key=HTTP_STATUS_CODE,
                label_value=str(response.status_code))

            _set_django_labels(tracer, request)

            tracer.end_span()
            tracer.end_trace()
        except Exception:  # pragma: NO COVER
            log.error('Failed to trace request', exc_info=True)
        finally:
            return response
