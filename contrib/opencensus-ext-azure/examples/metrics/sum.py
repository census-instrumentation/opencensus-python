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

import random
import time

from opencensus.ext.azure import metric_exporter
from opencensus.metrics.export import aggregation as aggregation_module
from opencensus.metrics.export import measure as measure_module
from opencensus.metrics.export import metric_producer as metric_module
from opencensus.metrics.export import view as view_module
from opencensus.tags import tag_map as tag_map_module

metrics = metric_module.metrics
view_manager = metrics.view_manager
metrics_recorder = metrics.metrics_recorder

CHIPS_EATEN_MEASURE = measure_module.MeasureFloat("chips_eaten", "number of chips eaten", "chips")
CHIPS_EATEN_VIEW = view_module.View('chips_eaten_view', "number of chips eaten", [], CHIPS_EATEN_MEASURE, aggregation_module.SumAggregation())

def main():
    # Enable metrics
    # Set the interval in seconds in which you want to send metrics
    exporter = metric_exporter.new_metrics_exporter(export_interval=5)
    view_manager.register_exporter(exporter)

    view_manager.register_view(CHIPS_EATEN_VIEW)
    mmap = metrics_recorder.new_measurement_map()
    tmap = tag_map_module.TagMap()

    for i in range(100):
        print(i)
        mmap.measure_int_put(CHIPS_EATEN_MEASURE, 1)
        mmap.record(tmap)
        time.sleep(1)

    print("Done recording metrics")


if __name__ == "__main__":
    main()
