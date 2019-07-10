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
from opencensus.metrics.export.gauge import Registry
from opencensus.metrics.export.metric_producer import MetricProducer


# Namespaces used in Azure Monitor
AVAILABLE_MEMORY = "\\Memory\\Available Bytes"


def get_available_memory():
    return psutil.virtual_memory().available


# Definitions taken from psutil docs
# https://psutil.readthedocs.io/en/latest/
# Available memory is defined as memory that can be given instantly to
# processes without the system going into swap
def get_available_memory_metric():
    gauge = DerivedLongGauge(
        AVAILABLE_MEMORY,
        'Amount of available memory in bytes',
        'byte',
        [])
    gauge.create_default_time_series(get_available_memory)
    return gauge


class AzureStandardMetricsProducer(MetricProducer):
    """Implementation of the producer of standard metrics.

    Includes Azure specific standard metrics.
    """
    def __init__(self):
        self.registry = Registry()
        self.registry.add_gauge(get_available_memory_metric())

    def get_metrics(self):
        return self.registry.get_metrics()


producer = AzureStandardMetricsProducer()
