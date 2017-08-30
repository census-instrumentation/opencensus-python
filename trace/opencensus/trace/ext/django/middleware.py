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
import threading

from opencensus.trace.ext import utils
from opencensus.trace.ext.django.config import settings
from opencensus.trace import labels_helper
from opencensus.trace import request_tracer

_thread_locals = threading.local()

HTTP_METHOD = labels_helper.STACKDRIVER_LABELS['HTTP_METHOD']
HTTP_URL = labels_helper.STACKDRIVER_LABELS['HTTP_URL']
HTTP_STATUS_CODE = labels_helper.STACKDRIVER_LABELS['HTTP_STATUS_CODE']

TRACER_THREAD_LOCAL_KEY = '_opencensus_django_request_tracer'

_DJANGO_TRACE_HEADER = 'HTTP_X_CLOUD_TRACE_CONTEXT'

log = logging.getLogger(__name__)


def _get_django_request():
    """Get Django request from thread local.

    :rtype: str
    :returns: Django request.
    """
    return getattr(_thread_locals, 'request', None)


def _get_current_request_tracer():
    """Get the current request tracer."""
    return getattr(_thread_locals, TRACER_THREAD_LOCAL_KEY, None)


def _set_django_labels(tracer, request):
    """Set the django related labels."""
    django_user = getattr(request, 'user', None)

    if django_user is None:
        return

    user_id = django_user.pk
    user_name = django_user.get_username()

    # User id is the django autofield for User model as the primary key
    if user_id is not None:
        tracer.add_label_to_spans('/django/user/id', user_id)

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

    def process_request(self, request):
        """Called on each request, before Django decides which view to execute.

        :type request: :class:`~django.http.request.HttpRequest`
        :param request: Django http request.
        """
        # Add the request to thread local
        _thread_locals.request = request

        try:
            # Start tracing this request
            header = get_django_header()
            propagator = self._propagator()
            span_context = propagator.from_header(header)

            # Reload the tracer with the new span context
            tracer = request_tracer.RequestTracer(
                span_context=span_context,
                sampler=self._sampler(),
                reporter=self._reporter(),
                propagator=propagator)

            setattr(_thread_locals, TRACER_THREAD_LOCAL_KEY, tracer)
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
                label_value=response.status_code)

            _set_django_labels(tracer, request)

            tracer.end_span()
            tracer.end_trace()
        except Exception:  # pragma: NO COVER
            log.error('Failed to trace request', exc_info=True)
        finally:
            return response
