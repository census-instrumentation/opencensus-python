# Copyright 2019, OpenCensus Authors
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

import requests

from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace import config_integration
from opencensus.trace.tracer import Tracer

if __name__ == '__main__':
    config_integration.trace_integrations(['requests'])
    # TODO: you need to specify the instrumentation key in the
    # APPINSIGHTS_INSTRUMENTATIONKEY environment variable.
    tracer = Tracer(exporter=AzureExporter())
    with tracer.span(name='parent'):
        with tracer.span(name='child'):
            response = requests.get(url='http://localhost:8080/')
            print(response.status_code)
            print(response.text)
