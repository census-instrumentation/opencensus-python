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
from azure.identity import ClientSecretCredential

from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer

tenant_id = "<tenant-id>"
client_id = "<client-id>"
client_secret = "<client-secret>"

credential = ClientSecretCredential(
    tenant_id=tenant_id,
    client_id=client_id,
    client_secret=client_secret
)

tracer = Tracer(
    exporter=AzureExporter(
        credential=credential, connection_string="<your-connection-string>"),
    sampler=ProbabilitySampler(1.0)
)

with tracer.span(name='foo'):
    print('Hello, World!')
