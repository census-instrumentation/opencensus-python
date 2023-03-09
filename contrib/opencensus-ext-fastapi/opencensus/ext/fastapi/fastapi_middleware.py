# Copyright 2022, OpenCensus Authors
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
import traceback
from typing import Union

from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from starlette.types import ASGIApp

from opencensus.trace import (
    attributes_helper,
    execution_context,
    integrations,
    print_exporter,
    samplers,
)
from opencensus.trace import span as span_module
from opencensus.trace import tracer as tracer_module
from opencensus.trace import utils
from opencensus.trace.blank_span import BlankSpan
from opencensus.trace.propagation import trace_context_http_header_format
from opencensus.trace.span import Span

HTTP_HOST = attributes_helper.COMMON_ATTRIBUTES["HTTP_HOST"]
HTTP_METHOD = attributes_helper.COMMON_ATTRIBUTES["HTTP_METHOD"]
HTTP_PATH = attributes_helper.COMMON_ATTRIBUTES["HTTP_PATH"]
HTTP_ROUTE = attributes_helper.COMMON_ATTRIBUTES["HTTP_ROUTE"]
HTTP_URL = attributes_helper.COMMON_ATTRIBUTES["HTTP_URL"]
HTTP_STATUS_CODE = attributes_helper.COMMON_ATTRIBUTES["HTTP_STATUS_CODE"]
ERROR_MESSAGE = attributes_helper.COMMON_ATTRIBUTES['ERROR_MESSAGE']
ERROR_NAME = attributes_helper.COMMON_ATTRIBUTES['ERROR_NAME']
STACKTRACE = attributes_helper.COMMON_ATTRIBUTES["STACKTRACE"]

module_logger = logging.getLogger(__name__)


class FastAPIMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware to automatically trace requests.

    :type app: :class: `~fastapi.FastAPI`
    :param app: A fastapi application.

    :type excludelist_paths: list
    :param excludelist_paths: Paths that do not trace.

    :type excludelist_hostnames: list
    :param excludelist_hostnames: Hostnames that do not trace.

    :type sampler: :class:`~opencensus.trace.samplers.base.Sampler`
    :param sampler: A sampler. It should extend from the base
                    :class:`.Sampler` type and implement
                    :meth:`.Sampler.should_sample`. Defaults to
                    :class:`.ProbabilitySampler`. Other options include
                    :class:`.AlwaysOnSampler` and :class:`.AlwaysOffSampler`.

    :type exporter: :class:`~opencensus.trace.base_exporter.exporter`
    :param exporter: An exporter. Default to
                     :class:`.PrintExporter`. The rest options are
                     :class:`.FileExporter`, :class:`.LoggingExporter` and
                     trace exporter extensions.

    :type propagator: :class: 'object'
    :param propagator: A propagator. Default to
                       :class:`.TraceContextPropagator`. The rest options
                       are :class:`.BinaryFormatPropagator`,
                       :class:`.GoogleCloudFormatPropagator` and
                       :class:`.TextFormatPropagator`.
    """

    def __init__(
        self,
        app: ASGIApp,
        excludelist_paths=None,
        excludelist_hostnames=None,
        sampler=None,
        exporter=None,
        propagator=None,
    ) -> None:
        super().__init__(app)
        self.excludelist_paths = excludelist_paths
        self.excludelist_hostnames = excludelist_hostnames
        self.sampler = sampler or samplers.AlwaysOnSampler()
        self.exporter = exporter or print_exporter.PrintExporter()
        self.propagator = (
            propagator or
            trace_context_http_header_format.TraceContextPropagator()
        )

        # pylint: disable=protected-access
        integrations.add_integration(integrations._Integrations.FASTAPI)

    def _prepare_tracer(self, request: Request) -> tracer_module.Tracer:
        span_context = self.propagator.from_headers(request.headers)
        tracer = tracer_module.Tracer(
            span_context=span_context,
            sampler=self.sampler,
            exporter=self.exporter,
            propagator=self.propagator,
        )
        return tracer

    def _before_request(self, span: Union[Span, BlankSpan], request: Request):
        span.span_kind = span_module.SpanKind.SERVER
        span.name = "[{}]{}".format(request.method, request.url)
        span.add_attribute(HTTP_HOST, request.url.hostname)
        span.add_attribute(HTTP_METHOD, request.method)
        span.add_attribute(HTTP_PATH, request.url.path)
        span.add_attribute(HTTP_URL, str(request.url))
        span.add_attribute(HTTP_ROUTE, request.url.path)
        execution_context.set_opencensus_attr(
            "excludelist_hostnames", self.excludelist_hostnames
        )

    def _after_request(self, span: Union[Span, BlankSpan], response: Response):
        span.add_attribute(HTTP_STATUS_CODE, response.status_code)

    def _handle_exception(self,
                          span: Union[Span, BlankSpan], exception: Exception):
        span.add_attribute(ERROR_NAME, exception.__class__.__name__)
        span.add_attribute(ERROR_MESSAGE, str(exception))
        span.add_attribute(
            STACKTRACE,
            "\n".join(traceback.format_tb(exception.__traceback__)))
        span.add_attribute(HTTP_STATUS_CODE, HTTP_500_INTERNAL_SERVER_ERROR)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:

        # Do not trace if the url is in the exclude list
        if utils.disable_tracing_url(str(request.url), self.excludelist_paths):
            return await call_next(request)

        try:
            tracer = self._prepare_tracer(request)
            span = tracer.start_span()
        except Exception:  # pragma: NO COVER
            module_logger.error("Failed to trace request", exc_info=True)
            return await call_next(request)

        try:
            self._before_request(span, request)
        except Exception:  # pragma: NO COVER
            module_logger.error("Failed to trace request", exc_info=True)

        try:
            response = await call_next(request)
        except Exception as err:  # pragma: NO COVER
            try:
                self._handle_exception(span, err)
                tracer.end_span()
                tracer.finish()
            except Exception:  # pragma: NO COVER
                module_logger.error("Failed to trace response", exc_info=True)
            raise err

        try:
            self._after_request(span, response)
            tracer.end_span()
            tracer.finish()
        except Exception:  # pragma: NO COVER
            module_logger.error("Failed to trace response", exc_info=True)

        return response
