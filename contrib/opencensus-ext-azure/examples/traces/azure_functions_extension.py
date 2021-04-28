# Copyright 2021, OpenCensus Authors
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

# TODO: Configure PYTHON_ENABLE_WORKER_EXTENSIONS = 1 function app setting.
# Ensure opencensus-ext-azure, opencensus-ext-requests and azure-functions
# are defined in your function app's requirements.txt and properly installed.
#
# For more information about getting started with Azure Functions, please visit
# https://aka.ms/functions-python-vscode
import json
import logging

import requests

from opencensus.ext.azure.extension.azure_functions import OpenCensusExtension

OpenCensusExtension.configure(
    libraries=['requests'],
    connection_string='InstrumentationKey=aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
)

def main(req, context):
    logging.info('Executing HttpTrigger with OpenCensus extension')

    with context.tracer.span("parent"):
        requests.get(url='http://example.com')

    return json.dumps({
        'method': req.method,
        'ctx_func_name': context.function_name,
        'ctx_func_dir': context.function_directory,
        'ctx_invocation_id': context.invocation_id,
        'ctx_trace_context_Traceparent': context.trace_context.Traceparent,
        'ctx_trace_context_Tracestate': context.trace_context.Tracestate,
    })
