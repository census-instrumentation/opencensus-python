#!/usr/bin/env python

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

import random
import time

from opencensus.ext.prometheus import stats_exporter as prometheus
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_key as tag_key_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.tags import tag_value as tag_value_module
from pprint import pprint

MiB = 1 << 20
FRONTEND_KEY = tag_key_module.TagKey("myorg_keys_frontend")
VIDEO_SIZE_MEASURE = measure_module.MeasureInt(
    "myorg_measures_video_size", "size of processed videos", "By")
VIDEO_SIZE_VIEW_NAME = "myorg_views_video_size"
VIDEO_SIZE_DISTRIBUTION = aggregation_module.DistributionAggregation(
    [0.0, 16.0 * MiB, 256.0 * MiB])
VIDEO_SIZE_VIEW = view_module.View(
    VIDEO_SIZE_VIEW_NAME, "processed video size over time", [FRONTEND_KEY],
    VIDEO_SIZE_MEASURE, VIDEO_SIZE_DISTRIBUTION)


def main():
    stats = stats_module.stats
    view_manager = stats.view_manager
    stats_recorder = stats.stats_recorder

    exporter = prometheus.new_stats_exporter(
        prometheus.Options(namespace="opencensus"))
    view_manager.register_exporter(exporter)

    # Register view.
    view_manager.register_view(VIDEO_SIZE_VIEW)

    # Sleep for [0, 10] milliseconds to fake work.
    time.sleep(random.randint(1, 10) / 1000.0)

    # Process video.
    # Record the processed video size.
    tag_value = tag_value_module.TagValue(str(random.randint(1, 10000)))
    tag_map = tag_map_module.TagMap()
    tag_map.insert(FRONTEND_KEY, tag_value)
    measure_map = stats_recorder.new_measurement_map()
    measure_map.measure_int_put(VIDEO_SIZE_MEASURE, 25 * MiB)
    measure_map.record(tag_map)

    # Get aggregated stats and print it to console.
    view_data = view_manager.get_view(VIDEO_SIZE_VIEW_NAME)
    pprint(vars(view_data))
    for k, v in view_data.tag_value_aggregation_data_map.items():
        pprint(k)
        pprint(vars(v))

    # Prevent main from exiting to see the data on prometheus
    # localhost:8000/metrics
    while True:
        pass


if __name__ == '__main__':
    main()
