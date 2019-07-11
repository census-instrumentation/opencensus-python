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

CARROTS_MEASURE = measure_module.MeasureInt("carrots",
                                            "number of carrots",
                                            "carrots")
CARROTS_VIEW = view_module.View("carrots_view",
                                "number of carrots",
                                [],
                                CARROTS_MEASURE,
                                aggregation_module.CountAggregation())

def main():
    # All you need is the next line. You can disable standard metrics by
    # passing in enable_standard_metrics=False into the constructor of
    # new_metrics_exporter()
    _exporter = metrics_exporter.new_metrics_exporter(instrumentation_key='70c241c9-206e-4811-82b4-2bc8a52170b9')
    view_manager.register_view(CARROTS_VIEW)
    mmap = stats_recorder.new_measurement_map()
    tmap = tag_map_module.TagMap()

    

    print(_exporter.max_batch_size)
    for i in range(100):
        print(psutil.virtual_memory())
        mmap.measure_int_put(CARROTS_MEASURE, 1000)
        mmap.record(tmap)
        time.sleep(5)

    print("Done recording metrics")


if __name__ == "__main__":
    main()
