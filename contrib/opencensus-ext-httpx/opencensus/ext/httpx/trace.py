import logging

import httpx
import wrapt

from opencensus.trace import (
    attributes_helper,
    exceptions_status,
    execution_context,
    integrations,
)
from opencensus.trace import span as span_module
from opencensus.trace import utils

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


log = logging.getLogger(__name__)

MODULE_NAME = "httpx"

HTTP_HOST = attributes_helper.COMMON_ATTRIBUTES["HTTP_HOST"]
HTTP_METHOD = attributes_helper.COMMON_ATTRIBUTES["HTTP_METHOD"]
HTTP_PATH = attributes_helper.COMMON_ATTRIBUTES["HTTP_PATH"]
HTTP_ROUTE = attributes_helper.COMMON_ATTRIBUTES["HTTP_ROUTE"]
HTTP_STATUS_CODE = attributes_helper.COMMON_ATTRIBUTES["HTTP_STATUS_CODE"]
HTTP_URL = attributes_helper.COMMON_ATTRIBUTES["HTTP_URL"]


def trace_integration(tracer=None):
    """Wrap the requests library to trace it."""
    log.info("Integrated module: {}".format(MODULE_NAME))

    if tracer is not None:
        # The execution_context tracer should never be None - if it has not
        # been set it returns a no-op tracer. Most code in this library does
        # not handle None being used in the execution context.
        execution_context.set_opencensus_tracer(tracer)

    wrapt.wrap_function_wrapper(
        MODULE_NAME, "Client.request", wrap_client_request
    )
    # pylint: disable=protected-access
    integrations.add_integration(integrations._Integrations.HTTPX)


def wrap_client_request(wrapped, instance, args, kwargs):
    """Wrap the session function to trace it."""
    # Check if request was sent from an exporter. If so, do not wrap.
    if execution_context.is_exporter():
        return wrapped(*args, **kwargs)

    method = kwargs.get("method") or args[0]
    url = kwargs.get("url") or args[1]

    excludelist_hostnames = execution_context.get_opencensus_attr(
        "excludelist_hostnames"
    )
    parsed_url = urlparse(url)
    if parsed_url.port is None:
        dest_url = parsed_url.hostname
    else:
        dest_url = "{}:{}".format(parsed_url.hostname, parsed_url.port)
    if utils.disable_tracing_hostname(dest_url, excludelist_hostnames):
        return wrapped(*args, **kwargs)

    path = parsed_url.path if parsed_url.path else "/"

    _tracer = execution_context.get_opencensus_tracer()
    _span = _tracer.start_span()

    _span.name = "{}".format(path)
    _span.span_kind = span_module.SpanKind.CLIENT

    try:
        tracer_headers = _tracer.propagator.to_headers(_tracer.span_context)
        kwargs.setdefault("headers", {}).update(tracer_headers)
    except Exception:  # pragma: NO COVER
        pass

    # Add the component type to attributes
    _tracer.add_attribute_to_current_span("component", "HTTP")

    # Add the requests host to attributes
    _tracer.add_attribute_to_current_span(HTTP_HOST, dest_url)

    # Add the requests method to attributes
    _tracer.add_attribute_to_current_span(HTTP_METHOD, method.upper())

    # Add the requests path to attributes
    _tracer.add_attribute_to_current_span(HTTP_PATH, path)

    # Add the requests url to attributes
    _tracer.add_attribute_to_current_span(HTTP_URL, url)

    try:
        result = wrapped(*args, **kwargs)
    except httpx.TimeoutException:
        _span.set_status(exceptions_status.TIMEOUT)
        raise
    except httpx.InvalidURL:
        _span.set_status(exceptions_status.INVALID_URL)
        raise
    except Exception as e:
        _span.set_status(exceptions_status.unknown(e))
        raise
    else:
        # Add the status code to attributes
        _tracer.add_attribute_to_current_span(
            HTTP_STATUS_CODE, result.status_code
        )
        _span.set_status(utils.status_from_http_code(result.status_code))
        return result
    finally:
        _tracer.end_span()
