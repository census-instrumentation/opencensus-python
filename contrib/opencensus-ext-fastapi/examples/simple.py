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
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.ext.fastapi.fastapi_middleware import FastAPIMiddleware
import uvicorn
from fastapi import FastAPI, Request

app = FastAPI()

middleware = FastAPIMiddleware(app)

@app.get("/")
async def root(request:Request):
    return {"message": request.client.host}


if __name__=="__main__":
    logger = logging.getLogger('werkzeug')
    logger.setLevel(logging.ERROR)
    uvicorn.run("simple:app", port=8888)