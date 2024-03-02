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
import asyncio
import logging

import wrapt
from aiohttp import InvalidURL, ServerTimeoutError
from yarl import URL

from opencensus.trace import (
    attributes_helper,
    exceptions_status,
    execution_context,
    utils,
)
from opencensus.trace.span import SpanKind

logger = logging.getLogger(__name__)

MODULE_NAME = "aiohttp"

COMPONENT = attributes_helper.COMMON_ATTRIBUTES["COMPONENT"]
HTTP_COMPONENT = "HTTP"
HTTP_HOST = attributes_helper.COMMON_ATTRIBUTES["HTTP_HOST"]
HTTP_METHOD = attributes_helper.COMMON_ATTRIBUTES["HTTP_METHOD"]
HTTP_PATH = attributes_helper.COMMON_ATTRIBUTES["HTTP_PATH"]
HTTP_ROUTE = attributes_helper.COMMON_ATTRIBUTES["HTTP_ROUTE"]
HTTP_STATUS_CODE = attributes_helper.COMMON_ATTRIBUTES["HTTP_STATUS_CODE"]
HTTP_URL = attributes_helper.COMMON_ATTRIBUTES["HTTP_URL"]


def trace_integration(tracer=None):
    """Wrap the aiohttp library to trace it."""
    logger.info("Integrated module: {}".format(MODULE_NAME))

    if tracer is not None:
        # The execution_context tracer should never be None - if it has not
        # been set it returns a no-op tracer. Most code in this library does
        # not handle None being used in the execution context.
        execution_context.set_opencensus_tracer(tracer)

    # Wrap Session class
    wrapt.wrap_function_wrapper(
        module=MODULE_NAME, name="ClientSession._request", wrapper=wrap_session_request
    )


async def wrap_session_request(wrapped, _, args, kwargs):
    """Wrap the session function to trace it."""
    if execution_context.is_exporter():
        return await wrapped(*args, **kwargs)

    method = kwargs.get("method") or args[0]
    str_or_url = kwargs.get("str_or_url") or args[1]
    try:
        url = URL(str_or_url)
    except ValueError as e:
        raise InvalidURL(str_or_url) from e

    excludelist_hostnames = execution_context.get_opencensus_attr(
        "excludelist_hostnames"
    )
    url_host_with_port = url.host + (f":{url.port}" if url.port else "")
    if utils.disable_tracing_hostname(url_host_with_port, excludelist_hostnames):
        return await wrapped(*args, **kwargs)

    url_path = url.path or "/"

    tracer = execution_context.get_opencensus_tracer()
    with tracer.span(name=url_path) as span:
        span.span_kind = SpanKind.CLIENT

        try:
            tracer_headers = tracer.propagator.to_headers(
                span_context=tracer.span_context,
            )
            kwargs.setdefault("headers", {}).update(tracer_headers)
        except Exception:
            pass

        span.add_attribute(
            attribute_key=COMPONENT,
            attribute_value=HTTP_COMPONENT,
        )
        span.add_attribute(
            attribute_key=HTTP_HOST,
            attribute_value=url_host_with_port,
        )
        span.add_attribute(
            attribute_key=HTTP_METHOD,
            attribute_value=method.upper(),
        )
        span.add_attribute(
            attribute_key=HTTP_PATH,
            attribute_value=url_path,
        )
        span.add_attribute(
            attribute_key=HTTP_URL,
            attribute_value=str(url),
        )

        try:
            result = await wrapped(*args, **kwargs)
        except (ServerTimeoutError, asyncio.TimeoutError):
            span.set_status(exceptions_status.TIMEOUT)
            raise
        except InvalidURL:
            span.set_status(exceptions_status.INVALID_URL)
            raise
        except Exception as e:
            span.set_status(exceptions_status.unknown(e))
            raise
        else:
            status_code = int(result.status)
            span.add_attribute(
                attribute_key=HTTP_STATUS_CODE,
                attribute_value=status_code,
            )
            span.set_status(utils.status_from_http_code(http_code=status_code))
            return result
