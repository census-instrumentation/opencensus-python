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

import google.auth

from opencensus.ext.stackdriver import stats_exporter as stackdriver
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_map as tag_map_module

# Create the measures
# The latency in milliseconds
m_latency_ms = measure_module.MeasureFloat(
    "task_latency", "The task latency in milliseconds", "ms")

# The stats recorder
stats = stats_module.stats
view_manager = stats.view_manager
stats_recorder = stats.stats_recorder

try:
    _, project_id = google.auth.default()
except google.auth.exceptions.DefaultCredentialsError:
    raise ValueError("Couldn't find Google Cloud credentials, set the "
                     "project ID with 'gcloud set project'")

latency_view = view_module.View(
    "task_latency_distribution",
    "The distribution of the task latencies",
    [],
    m_latency_ms,
    # Latency in buckets: [>=0ms, >=100ms, >=200ms, >=400ms, >=1s, >=2s, >=4s]
    aggregation_module.DistributionAggregation(
        [100.0, 200.0, 400.0, 1000.0, 2000.0, 4000.0]))


def main():
    # Enable metrics
    exporter = stackdriver.new_stats_exporter(
        stackdriver.Options(project_id=project_id))
    view_manager.register_exporter(exporter)

    view_manager.register_view(latency_view)
    mmap = stats_recorder.new_measurement_map()
    tmap = tag_map_module.TagMap()

    for i in range(100):
        ms = random.random() * 5 * 1000
        print("Latency {0}:{1}".format(i, ms))
        mmap.measure_float_put(m_latency_ms, ms)
        mmap.record(tmap)
        time.sleep(1)

    print("Done recording metrics")


if __name__ == "__main__":
    main()
