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
import sys

from opencensus.trace import attributes_helper
from opencensus.trace import execution_context
from opencensus.trace import span as span_module
from opencensus.trace import utils

PYTHON2 = sys.version_info.major == 2

if PYTHON2:
    import httplib
else:
    import http.client as httplib

log = logging.getLogger(__name__)

MODULE_NAME = 'httplib'
HTTPLIB_REQUEST_FUNC = 'request'
HTTPLIB_RESPONSE_FUNC = 'getresponse'

HTTP_METHOD = attributes_helper.COMMON_ATTRIBUTES['HTTP_METHOD']
HTTP_URL = attributes_helper.COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = attributes_helper.COMMON_ATTRIBUTES['HTTP_STATUS_CODE']


def trace_integration(tracer=None):
    """Wrap the httplib to trace."""
    log.info('Integrated module: {}'.format(MODULE_NAME))

    # Wrap the httplib request function
    request_func = getattr(
        httplib.HTTPConnection, HTTPLIB_REQUEST_FUNC)
    wrapped_request = wrap_httplib_request(request_func)
    setattr(httplib.HTTPConnection, request_func.__name__, wrapped_request)

    # Wrap the httplib response function
    response_func = getattr(
        httplib.HTTPConnection, HTTPLIB_RESPONSE_FUNC)
    wrapped_response = wrap_httplib_response(response_func)
    setattr(httplib.HTTPConnection, response_func.__name__, wrapped_response)


def wrap_httplib_request(request_func):
    """Wrap the httplib request function to trace. Create a new span and update
    and close the span in the response later.
    """

    def call(self, method, url, body, headers, *args, **kwargs):
        _tracer = execution_context.get_opencensus_tracer()
        blacklist_hostnames = execution_context.get_opencensus_attr(
            'blacklist_hostnames')
        dest_url = '{}:{}'.format(self._dns_host, self.port)
        if utils.disable_tracing_hostname(dest_url, blacklist_hostnames):
            return request_func(self, method, url, body,
                                headers, *args, **kwargs)
        _span = _tracer.start_span()
        _span.span_kind = span_module.SpanKind.CLIENT
        _span.name = '[httplib]{}'.format(request_func.__name__)

        # Add the request url to attributes
        _tracer.add_attribute_to_current_span(HTTP_URL, url)

        # Add the request method to attributes
        _tracer.add_attribute_to_current_span(HTTP_METHOD, method)

        # Store the current span id to thread local.
        execution_context.set_opencensus_attr(
            'httplib/current_span_id', _span.span_id)
        try:
            headers = headers.copy()
            headers.update(_tracer.propagator.to_headers(
                _span.context_tracer.span_context))
        except Exception:  # pragma: NO COVER
            pass
        return request_func(self, method, url, body, headers, *args, **kwargs)

    return call


def wrap_httplib_response(response_func):
    """Wrap the httplib response function to trace.

    If there is a corresponding httplib request span, update and close it.
    If not, return the response.
    """

    def call(self, *args, **kwargs):
        _tracer = execution_context.get_opencensus_tracer()
        current_span_id = execution_context.get_opencensus_attr(
            'httplib/current_span_id')

        span = _tracer.current_span()

        # No corresponding request span is found, request not traced.
        if not span or span.span_id != current_span_id:
            return response_func(self, *args, **kwargs)

        result = response_func(self, *args, **kwargs)

        # Add the status code to attributes
        _tracer.add_attribute_to_current_span(
            HTTP_STATUS_CODE, str(result.status))

        _tracer.end_span()
        return result

    return call
