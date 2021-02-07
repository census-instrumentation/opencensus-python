# Opencensus imports
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.trace.span import SpanKind
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

HTTP_URL = COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = COMMON_ATTRIBUTES['HTTP_STATUS_CODE']

class FastAPIMiddleware(BaseHTTPMiddleware):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def _before_request(request: Request, tracer):
        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_URL,
            attribute_value=str(request.url))

    @staticmethod
    def _after_request(response, tracer):
        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_STATUS_CODE,
            attribute_value=response.status_code)
    
    async def dispatch(self, request: Request, call_next):
        exporter = request.app.trace_exporter
        tracer = Tracer(exporter=exporter,sampler=ProbabilitySampler(1.0))
        with tracer.span("main") as span:
            span.span_kind = SpanKind.SERVER

            self._before_request(request, tracer)
            response = await call_next(request)
            self._after_request(response, tracer)

        return response