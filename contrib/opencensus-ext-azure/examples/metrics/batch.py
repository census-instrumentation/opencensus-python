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
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_map as tag_map_module

stats = stats_module.stats
view_manager = stats.view_manager
stats_recorder = stats.stats_recorder

COUNT_MEASURE = measure_module.MeasureInt("count",
                                          "number count",
                                          "number")
COUNT_VIEW = view_module.View("count_view",
                              "number count",
                              ["tag1"],
                              COUNT_MEASURE,
                              aggregation_module.CountAggregation())

SUM_MEASURE = measure_module.MeasureFloat("sum",
                                          "number sum",
                                          "number")
SUM_VIEW = view_module.View("sum_view",
                            "number sum",
                            ["tag1"],
                            SUM_MEASURE,
                            aggregation_module.SumAggregation())


def main():
    # Enable metrics
    # Set the interval in seconds in which you want to send metrics
    exporter = metrics_exporter.new_metrics_exporter(
                                export_interval=2.0,
                                max_batch_size=1)
    view_manager.register_exporter(exporter)

    view_manager.register_view(COUNT_VIEW)
    view_manager.register_view(SUM_VIEW)
    mmap = stats_recorder.new_measurement_map()
    tmap = tag_map_module.TagMap()
    tmap.insert("tag1", "tag_value")

    mmap.measure_int_put(COUNT_MEASURE, 1)
    mmap.measure_float_put(SUM_MEASURE, 3)
    mmap.record(tmap)
    time.sleep(30)

    print("Done recording metrics")


if __name__ == "__main__":
    main()
