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


# Definitions taken from psutil docs
# https://psutil.readthedocs.io/en/latest/
class StandardMetricsType(object):
    # Memory that can be given instantly to
    # processes without the system going into swap
    AVAILABLE_MEMORY = "\\Memory\\Available Bytes"


class StandardMetricsProducer(MetricProducer):

    def __init__(self):
        self.registry = Registry()
        self.setup()

    def setup(self):
        available_memory_gauge = DerivedLongGauge(StandardMetricsType.AVAILABLE_MEMORY,
            'Amount of available memory in bytes',
            'byte',
            [])
        available_memory_gauge.create_default_time_series(self.get_available_memory)
        self.registry.add_gauge(available_memory_gauge)

    def get_available_memory(self):
        return psutil.virtual_memory().available

    def get_metrics(self):
        for metric in self.registry.get_metrics():
            yield metric

producer = StandardMetricsProducer()
