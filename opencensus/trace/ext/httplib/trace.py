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
import time

from retrying import retry

from opencensus.trace import execution_context

PYTHON2 = sys.version_info.major == 2

if PYTHON2:
    import httplib
else:
    import http.client as httplib

log = logging.getLogger(__name__)

MODULE_NAME = 'httplib'
HTTPLIB_REQUEST_FUNC = 'request'
HTTPLIB_RESPONSE_FUNC = 'getresponse'

RETRY_WAIT_PERIOD = 1 # Wait 1 seconds between each retry
RETRY_MAX_ATTEMPT = 5 # Retry 5 times


def trace_integration():
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
    """Wrap the httplib request function to trace. Create a new span and update or
    close the span in the response later.
    """
    def call(method, url, *args, **kwargs):
        _tracer = execution_context.get_opencensus_tracer()
        _span = _tracer.start_span()
        _span.name = '[httplib]{}'.format(request_func.__name__)

        # Add the request url to attributes
        _tracer.add_attribute_to_current_span('httplib/request/url', url)

        # Store the current span id to thread local.
        execution_context.set_opencensus_attr(
            'httplib/current_span_id', _span.span_id)

        return request_func(method, url, *args, **kwargs)

    return call


def wrap_httplib_response(response_func):
    """Wrap the httplib response function to trace.

    If there is a corresponding httplib request span, update and close it.
    If not, return.
    """
    def call(*args, **kwargs):
        _tracer = execution_context.get_opencensus_tracer()
        current_span_id = execution_context.get_opencensus_attr(
            'httplib/current_span_id')

        span = _tracer.current_span()

        # No corresponding request span is found, request not traced.
        if span.span_id != current_span_id:
            return response_func(*args, **kwargs)

        result = response_func(*args, **kwargs)

        # Add the status code to attributes
        _tracer.add_attribute_to_current_span(
            'httplib/response/status_code', str(result.status))

        _tracer.end_span()
        return result

    return call
