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

from opencensus.metrics.export import measure

class MetricType(object):
    MEASURE = 0

class Meter(object):
    """ Meter is a simple, interface that allows users to record measurements (metrics).

        There are two ways to record measurements:

        Record raw measurements, and defer defining the aggregation and the labels for the exported
               Metric. This should be used in libraries like gRPC to record measurements like
               "server_latency" or "received_bytes".
        Record pre-defined aggregation data (or already aggregated data). This should be used to
              report cpu/memory usage, or simple metrics like "queue_length".
    """  # noqa

    def __init__(self):
        self._builders = {}

    @property
    def builders(self):
        return self._builders

    def measureBuilder(self, name, metric_type, description, unit):
        if name is None:
            raise ValueError("Name cannot be null") 
        if MetricType.MEASURE not in self._builders:
            self._builders[MetricType.MEASURE] = measure.Builder(name, metric_type, description, unit).build()
        return self._builders[MetricType.MEASURE]

    def record(self, metric_type, value):
        if metric_type in self._builders:
            self._builders[metric_type].create_measurement(value)
        

