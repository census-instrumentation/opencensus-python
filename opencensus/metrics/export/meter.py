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
from opencensus.metrics.export import execution_context


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
        if execution_context.get_measurements_map() == {}:
            execution_context.set_measurements_map(dict())

        self.measurements_map = execution_context.get_measurements_map()

    def create_metric(self, name, metric_type, description, unit, label_keys, label_values):
        # TODO
        return

    def create_measure(self, name, measure_type=measure.MeasureType.DOUBLE, description="", unit="", aggregation_type=measure.AggregationType.COUNT):
        if name is None:
            raise ValueError("Name cannot be null") 
        return measure.Measure(name, measure_type, description, unit, aggregation_type)

    def record(self, measure, measurements):
        self.measurements_map[measure] = measurements