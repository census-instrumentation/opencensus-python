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

REQUEST_MEASURE = measure_module.MeasureFloat("Requests",
                                              "number of requests",
                                              "requests")
NUM_REQUESTS_VIEW = view_module.View("Number of Requests",
                                     "number of requests",
                                     ["url"],
                                     REQUEST_MEASURE,
                                     aggregation_module.SumAggregation())


def main():
    # Enable metrics
    # Set the interval in seconds in which you want to send metrics
    exporter = metrics_exporter.new_metrics_exporter()
    view_manager.register_exporter(exporter)

    view_manager.register_view(NUM_REQUESTS_VIEW)
    mmap = stats_recorder.new_measurement_map()
    tmap = tag_map_module.TagMap()
    tmap.insert("url", "http://example.com")

    for i in range(100):
        print(i)
        mmap.measure_int_put(REQUEST_MEASURE, i)
        mmap.record(tmap)
        time.sleep(1)

    print("Done recording metrics")


if __name__ == "__main__":
    main()
