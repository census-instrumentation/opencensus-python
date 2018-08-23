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
import requests
import wrapt

from opencensus.trace import attributes_helper
from opencensus.trace import execution_context
from opencensus.trace import span as span_module

log = logging.getLogger(__name__)

MODULE_NAME = 'requests'

REQUESTS_WRAP_METHODS = ['get', 'post', 'put', 'delete', 'head', 'options']
SESSION_WRAP_METHODS = 'request'
SESSION_CLASS_NAME = 'Session'

HTTP_URL = attributes_helper.COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = attributes_helper.COMMON_ATTRIBUTES['HTTP_STATUS_CODE']


def trace_integration(tracer=None):
    """Wrap the requests library to trace it."""
    log.info('Integrated module: {}'.format(MODULE_NAME))

    execution_context.set_opencensus_tracer(tracer)

    # Wrap the requests functions
    for func in REQUESTS_WRAP_METHODS:
        requests_func = getattr(requests, func)
        wrapped = wrap_requests(requests_func)
        setattr(requests, requests_func.__name__, wrapped)

    # Wrap Session class
    wrapt.wrap_function_wrapper(
        MODULE_NAME, 'Session.request', wrap_session_request)


def wrap_requests(requests_func):
    """Wrap the requests function to trace it."""
    def call(url, *args, **kwargs):
        _tracer = execution_context.get_opencensus_tracer()
        _span = _tracer.start_span()
        _span.name = '[requests]{}'.format(requests_func.__name__)
        _span.span_kind = span_module.SpanKind.CLIENT

        # Add the requests url to attributes
        _tracer.add_attribute_to_current_span(HTTP_URL, url)

        result = requests_func(url, *args, **kwargs)

        # Add the status code to attributes
        _tracer.add_attribute_to_current_span(
            HTTP_STATUS_CODE, str(result.status_code))

        _tracer.end_span()
        return result

    return call


def wrap_session_request(wrapped, instance, args, kwargs):
    """Wrap the session function to trace it."""
    method = kwargs.get('method') or args[0]
    url = kwargs.get('url') or args[1]
    _tracer = execution_context.get_opencensus_tracer()
    _span = _tracer.start_span()

    _span.name = '[requests]{}'.format(method)
    _span.span_kind = span_module.SpanKind.CLIENT

    # Add the requests url to attributes
    _tracer.add_attribute_to_current_span(HTTP_URL, url)

    result = wrapped(*args, **kwargs)

    # Add the status code to attributes
    _tracer.add_attribute_to_current_span(
        HTTP_STATUS_CODE, str(result.status_code))

    _tracer.end_span()
    return result
