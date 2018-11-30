# Copyright 2018, OpenCensus Authors
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
import random
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats.exporters import stackdriver_exporter as stackdriver
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_key as tag_key_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.tags import tag_value as tag_value_module

MiB = 1 << 20
FRONTEND_KEY = tag_key_module.TagKey("my.org/keys/frontend")
VIDEO_SIZE_MEASURE = measure_module.MeasureInt(
    "my.org/measure/video_size_test2", "size of processed videos", "By")
VIDEO_SIZE_VIEW_NAME = "my.org/views/video_size_test2"
VIDEO_SIZE_DISTRIBUTION = aggregation_module.DistributionAggregation(
    [0.0, 16.0 * MiB, 256.0 * MiB])
VIDEO_SIZE_VIEW = view_module.View(
    VIDEO_SIZE_VIEW_NAME, "processed video size over time", [FRONTEND_KEY],
    VIDEO_SIZE_MEASURE, VIDEO_SIZE_DISTRIBUTION)

stats = stats_module.Stats()
view_manager = stats.view_manager
stats_recorder = stats.stats_recorder

exporter = stackdriver.new_stats_exporter(
    stackdriver.Options(project_id="opencenus-node"))
view_manager.register_exporter(exporter)

# Register view.
view_manager.register_view(VIDEO_SIZE_VIEW)

# Sleep for [0, 10] milliseconds to fake work.
time.sleep(random.randint(1, 10) / 1000.0)

# Process video.
# Record the processed video size.
tag_value = tag_value_module.TagValue(str(1200))
tag_map = tag_map_module.TagMap()
tag_map.insert(FRONTEND_KEY, tag_value)
measure_map = stats_recorder.new_measurement_map()
measure_map.measure_int_put(VIDEO_SIZE_MEASURE, 25 * MiB)

measure_map.record(tag_map)
