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
import sys
import time
import unittest

from opencensus.ext.prometheus import stats_exporter as prometheus
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_key as tag_key_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.tags import tag_value as tag_value_module


class TestPrometheusStats(unittest.TestCase):
    def test_prometheus_stats(self):

        method_key = tag_key_module.TagKey("method")
        request_count_measure = measure_module.MeasureInt(
            "request_count", "number of requests", "1")
        request_count_view_name = "request_count_view"
        count_agg = aggregation_module.CountAggregation()
        request_count_view = view_module.View(
            request_count_view_name,
            "number of requests broken down by methods",
            [method_key], request_count_measure, count_agg)
        stats = stats_module.Stats()
        view_manager = stats.view_manager
        stats_recorder = stats.stats_recorder

        exporter = prometheus.new_stats_exporter(
            prometheus.Options(namespace="opencensus", port=9303))
        view_manager.register_exporter(exporter)

        view_manager.register_view(request_count_view)

        time.sleep(random.randint(1, 10) / 1000.0)

        method_value_1 = tag_value_module.TagValue("some method")
        tag_map_1 = tag_map_module.TagMap()
        tag_map_1.insert(method_key, method_value_1)
        measure_map_1 = stats_recorder.new_measurement_map()
        measure_map_1.measure_int_put(request_count_measure, 1)
        measure_map_1.record(tag_map_1)

        method_value_2 = tag_value_module.TagValue("some other method")
        tag_map_2 = tag_map_module.TagMap()
        tag_map_2.insert(method_key, method_value_2)
        measure_map_2 = stats_recorder.new_measurement_map()
        measure_map_2.measure_int_put(request_count_measure, 1)
        measure_map_2.record(tag_map_2)
        measure_map_2.record(tag_map_2)

        if sys.version_info > (3, 0):
            import urllib.request
            contents = urllib.request.urlopen(
                "http://localhost:9303/metrics").read()
        else:
            import urllib2
            contents = urllib2.urlopen("http://localhost:9303/metrics").read()

        self.assertIn(b'# TYPE opencensus_request_count_view_total counter',
                      contents)
        self.assertIn(b'opencensus_request_count_view_total'
                      b'{method="some method"} 1.0',
                      contents)
        self.assertIn(b'opencensus_request_count_view_total'
                      b'{method="some other method"} 2.0',
                      contents)
