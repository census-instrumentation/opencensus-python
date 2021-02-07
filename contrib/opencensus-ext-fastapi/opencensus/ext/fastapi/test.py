# Opencensus imports
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.trace.span import SpanKind
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES
# FastAPI imports
from fastapi import FastAPI, Request
from starlette.responses import Response
# uvicorn
import uvicorn
from fastapi_middleware import FastAPIMiddleware

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    app.trace_exporter = AzureExporter(connection_string=f'InstrumentationKey=<InstrumentationKey>')

app.add_middleware(FastAPIMiddleware)

@app.get("/")
async def root():
    return "Hello World!"

if __name__ == '__main__':
    uvicorn.run("test:app", host="127.0.0.1", port=8888, log_level="info")