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

import psutil

from opencensus.metrics.export.gauge import DerivedLongGauge
from opencensus.metrics.export.standard_metrics import BaseStandardMetric
from opencensus.metrics.export.standard_metrics import StandardMetricsProducer


class StandardMetricsType(object):
    AVAILABLE_MEMORY = "\\Memory\\Available Bytes"


# Definitions taken from psutil docs
# https://psutil.readthedocs.io/en/latest/
class AvailableMemoryStandardMetric(BaseStandardMetric):
    # Avaliable memory is defined as memory that can be given instantly to
    # processes without the system going into swap
    def __init__(self):
        super(AvailableMemoryStandardMetric, self).__init__()

    def register(self, registry):
        available_memory_gauge = DerivedLongGauge(
            StandardMetricsType.AVAILABLE_MEMORY,
            'Amount of available memory in bytes',
            'byte',
            [])
        available_memory_gauge.create_default_time_series(
            self.get_available_memory)
        registry.add_gauge(available_memory_gauge)

    def get_available_memory(self):
        return psutil.virtual_memory().available  # pragma: NO COVER


class AzureStandardMetricsProducer(StandardMetricsProducer):
    # Implementation of the producer of standard metrics
    def __init__(self):
        super(AzureStandardMetricsProducer, self).__init__()
        self.metrics = []
        self.init_metrics()

    def init_metrics(self):
        self.metrics.append(AvailableMemoryStandardMetric())
        self.register_metrics(self.metrics)


producer = AzureStandardMetricsProducer()
