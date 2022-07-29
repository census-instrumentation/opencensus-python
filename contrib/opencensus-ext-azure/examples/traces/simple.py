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

from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer

def callback(envelopes):
    print(envelopes)
    return True

# TODO: you need to specify the instrumentation key in a connection string
# and place it in the APPLICATIONINSIGHTS_CONNECTION_STRING
# environment variable.
exporter = AzureExporter()
exporter.add_telemetry_processor(callback)
tracer = Tracer(exporter=exporter, sampler=ProbabilitySampler(1.0))

with tracer.span(name='foo'):
    with tracer.span("quark") as span:
        print('Hello, World!')

input(...)