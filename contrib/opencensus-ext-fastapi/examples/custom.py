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

import os

from fastapi import FastAPI, Request
import grpc
import mysql.connector
import psycopg2
import requests
import uvicorn
import hello_world_pb2
import hello_world_pb2_grpc
from opencensus.ext.fastapi.fastapi_middleware import FastAPIMiddleware
from opencensus.ext.grpc import client_interceptor
from opencensus.ext.stackdriver import trace_exporter as stackdriver_exporter
from opencensus.trace import config_integration, samplers
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler

INTEGRATIONS = ['mysql', 'logging']

DB_HOST = '127.0.0.1'

PROJECT = os.environ.get('GCLOUD_PROJECT_PYTHON')

# MySQL settings
MYSQL_PASSWORD = os.environ.get('SYSTEST_MYSQL_PASSWORD')

# hello_world_server location
HELLO_WORLD_HOST_PORT = 'localhost:50051'

app = FastAPI()

# optional TODO: test with stack driver

# Enable tracing, configure the trace params, send traces to Azure Trace
exporter = AzureExporter(connection_string="InstrumentationKey=<InstrumentationKey>")
sampler = ProbabilitySampler(rate=1.0)

middleware = FastAPIMiddleware(
    app,
    exporter=exporter,
    sampler=sampler,
)

config_integration.trace_integrations(INTEGRATIONS)

# cache of (stub_cls, hostport) -> grpc stub
_stub_cache = {}


@app.route('/')
def hello():
    return 'Hello world!'

# optional
@app.route('/mysql')
def mysql_query():
    try:
        return None

    except Exception:
        msg = "Query failed. Check your env vars for connection settings."
        return None

if __name__ == '__main__':
    uvicorn.run("custom:app", port=8888, reload=True, debug=True, workers=3)
