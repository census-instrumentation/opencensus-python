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
from azure.identity import VisualStudioCodeCredential

from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer

# This example uses VisualStudioCodeCredential, which authenticates
# an Azure user signed into Visual Studio Code
# See https://github.com/Azure/azure-sdk-for-python/blob/master/sdk/identity/azure-identity/README.md#credential-classes  # noqa: E501
# for different credential classes.
credential = VisualStudioCodeCredential()

# TODO: you need to specify the instrumentation key in a connection string
# and place it in the APPLICATIONINSIGHTS_CONNECTION_STRING
# environment variable.
tracer = Tracer(
    exporter=AzureExporter(credential=credential),
    sampler=ProbabilitySampler(1.0)
)


with tracer.span(name='foo'):
    print('Hello, World!')
input(...)
