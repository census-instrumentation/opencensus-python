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

import logging

from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace import config_integration
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer

config_integration.trace_integrations(['logging'])

logger = logging.getLogger(__name__)

# TODO: you need to specify the instrumentation key in the
# APPINSIGHTS_INSTRUMENTATIONKEY environment variable.
handler = AzureLogHandler()
logger.addHandler(handler)

tracer = Tracer(exporter=AzureExporter(), sampler=ProbabilitySampler(1.0))

logger.warning('Before the span')
with tracer.span(name='test'):
    logger.warning('In the span')
logger.warning('After the span')
