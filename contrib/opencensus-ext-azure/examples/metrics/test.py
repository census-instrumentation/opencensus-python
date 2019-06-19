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
from opencensus.metrics.export.metric_producer import MetricProducer

from opencensus.tags import tag_map as tag_map_module

meter_ = meter.Meter()
meter_.measureBuilder("test_count3", measure.MeasureType.LONG, "test_desc", "test_unit")
metrics_exporter.new_metrics_exporter(meter_, export_interval=2, instrumentation_key='70c241c9-206e-4811-82b4-2bc8a52170b9')

def main():

    tmap = tag_map_module.TagMap()

    for i in range(10):
        meter_.record(meter.MetricType.MEASURE, i)
        time.sleep(2)

    print("Done recording metrics")


if __name__ == "__main__":
    main()
