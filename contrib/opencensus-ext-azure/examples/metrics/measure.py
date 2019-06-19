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

import time

from opencensus.ext.azure import metrics_exporter
from opencensus.metrics.export import meter
from opencensus.metrics.export import measure
from opencensus.metrics.export import metrics_producer

mp = metrics_producer.metrics_producer
meter = mp.meter
_measure = meter.create_measure("test_count4",
                                measure.MeasureType.LONG,
                                "test_desc",
                                "test_unit",
                                measure.AggregationType.COUNT)

def main():
    metrics_exporter.new_metrics_exporter(export_interval=2)

    measurements = []
    for i in range(10):
        measurements.append(_measure.create_long_measurement(i))
    
    meter.record(_measure, measurements)
    time.sleep(5)
    print("Done recording metrics")


if __name__ == "__main__":
    main()
