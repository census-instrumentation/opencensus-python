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

from opencensus.trace import tracer as tracer_module
from opencensus.ext.azure.protocol import *
from opencensus.ext.azure.util import azure_monitor_context
from opencensus.ext.azure.trace_exporter import AzureExporter

import json
import requests

envelope = Envelope(
    iKey='33018a74-404a-45ba-ba5d-079020eb7bba',
    name='Microsoft.ApplicationInsights.Event',
    tags=azure_monitor_context,
)
envelope.time = '2019-04-05T23:59:59.999999Z'
envelope.data = {
    'baseData': Event(name='Hello, world!'),
    'baseType': 'EventData'
}
print(envelope)
print(json.dumps(envelope))


response = requests.post(
    url='https://dc.services.visualstudio.com/v2/track',
    data=json.dumps([envelope]),
    headers={
        'Accept': 'application/json',
        'Content-Type' : 'application/json; charset=utf-8',
    },
)
print(response.status_code)
print(response.json())

azure_monitor_exporter = AzureExporter(config={
    'InstrumentationKey': '33018a74-404a-45ba-ba5d-079020eb7bba',
})
tracer = tracer_module.Tracer(exporter=azure_monitor_exporter)

# pip install -e . && python examples\scratch.py

if __name__ == '__main__':
    with tracer.span(name='foo'):
        print('Hello, world!')
