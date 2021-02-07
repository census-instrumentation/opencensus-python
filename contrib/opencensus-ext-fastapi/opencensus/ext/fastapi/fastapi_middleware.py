
# HTTP_HOST = attributes_helper.COMMON_ATTRIBUTES['HTTP_HOST']
# HTTP_METHOD = attributes_helper.COMMON_ATTRIBUTES['HTTP_METHOD']
# HTTP_PATH = attributes_helper.COMMON_ATTRIBUTES['HTTP_PATH']
# HTTP_ROUTE = attributes_helper.COMMON_ATTRIBUTES['HTTP_ROUTE']
# HTTP_URL = attributes_helper.COMMON_ATTRIBUTES['HTTP_URL']
# HTTP_STATUS_CODE = attributes_helper.COMMON_ATTRIBUTES['HTTP_STATUS_CODE']

# BLACKLIST_PATHS = 'BLACKLIST_PATHS'
# BLACKLIST_HOSTNAMES = 'BLACKLIST_HOSTNAMES'

# log = logging.getLogger(__name__)
# Opencensus imports

from opencensus.trace.propagation.trace_context_http_header_format import TraceContextPropagator
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.trace.span import SpanKind
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

HTTP_HOST = COMMON_ATTRIBUTES['HTTP_HOST']
HTTP_METHOD = COMMON_ATTRIBUTES['HTTP_METHOD']
HTTP_PATH = COMMON_ATTRIBUTES['HTTP_PATH']
HTTP_URL = COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = COMMON_ATTRIBUTES['HTTP_STATUS_CODE']

class FastAPIMiddleware(BaseHTTPMiddleware):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._trace_propagator =TraceContextPropagator()

    @staticmethod
    def _before_request(request: Request, tracer):
        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_URL,
            attribute_value=str(request.url))
        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_HOST,
            attribute_value=request.client.host)
        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_METHOD,
            attribute_value=request.method)
        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_PATH,
            attribute_value=str(request.url.path))

    @staticmethod
    def _after_request(response, tracer):
        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_STATUS_CODE,
            attribute_value=response.status_code)
    
    async def dispatch(self, request: Request, call_next):
        exporter = request.app.trace_exporter
        span_context = self._trace_propagator.from_headers(request.headers)
        tracer = Tracer(span_context=span_context, sampler=ProbabilitySampler(0.1),
                                    propagator=self._trace_propagator, exporter=exporter)
        with tracer.span("main") as span:
            span.span_kind = SpanKind.SERVER

            self._before_request(request, tracer)
            response = await call_next(request)
            self._after_request(response, tracer)

        return response