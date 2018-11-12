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

from datetime import datetime
import mock
import unittest

from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.stats import view_data as view_data_module
from opencensus.stats.exporters import prometheus_exporter as prometheus
from opencensus.tags import tag_key as tag_key_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.tags import tag_value as tag_value_module


MiB = 1 << 20
FRONTEND_KEY = tag_key_module.TagKey("my.org/keys/frontend")
FRONTEND_KEY_FLOAT = tag_key_module.TagKey("my.org/keys/frontend-FLOAT")
FRONTEND_KEY_INT = tag_key_module.TagKey("my.org/keys/frontend-INT")
FRONTEND_KEY_STR = tag_key_module.TagKey("my.org/keys/frontend-INT")

VIDEO_SIZE_MEASURE = measure_module.MeasureInt(
    "my.org/measure/video_size_test2", "size of processed videos", "By")

VIDEO_SIZE_MEASURE_FLOAT = measure_module.MeasureFloat(
    "my.org/measure/video_size_test-float", "size of processed videos-float",
    "By")

VIDEO_SIZE_VIEW_NAME = "my.org/views/video_size_test2"
VIDEO_SIZE_DISTRIBUTION = aggregation_module.DistributionAggregation(
    [0.0, 16.0 * MiB, 256.0 * MiB])
VIDEO_SIZE_VIEW = view_module.View(
    VIDEO_SIZE_VIEW_NAME, "processed video size over time", [FRONTEND_KEY],
    VIDEO_SIZE_MEASURE, VIDEO_SIZE_DISTRIBUTION)
REGISTERED_VIEW = {
    'test1_my.org/views/video_size_test2-my.org/keys/frontend': {
        'documentation': 'processed video size over time',
        'labels': ['my.org/keys/frontend'],
        'name': 'test1_my.org/views/video_size_test2'
    }
}

REGISTERED_VIEW2 = {
    'opencensus_my.org/views/video_size_test2-my.org/keys/frontend': {
        'documentation': 'processed video size over time',
        'labels': ['my.org/keys/frontend'],
        'name': 'opencensus_my.org/views/video_size_test2'
    }
}


class TestOptionsPrometheus(unittest.TestCase):
    def test_options_constructor(self):
        option = prometheus.Options("test1")
        self.assertEqual(option.namespace, "test1")

    def test_options_constructor_with_params(self):
        registry = mock.Mock()
        option = prometheus.Options("test1", 8001, "localhost", registry)
        self.assertEqual(option.namespace, "test1")
        self.assertEqual(option.port, 8001)
        self.assertEqual(option.address, "localhost")
        self.assertEqual(option.registry, registry)


class TestCollectorPrometheus(unittest.TestCase):
    def test_collector_constructor(self):
        options = prometheus.Options("test1")
        self.assertEqual(options.namespace, "test1")
        collector = prometheus.Collector(options)
        self.assertEqual(options, collector.options)

    def test_collector_constructor_with_params(self):
        registry = mock.Mock()
        view_data = mock.Mock()
        options = prometheus.Options("test1", 8001, "localhost", registry)
        self.assertEqual(options.namespace, "test1")
        self.assertEqual(options.port, 8001)
        self.assertEqual(options.address, "localhost")
        self.assertEqual(options.registry, registry)

        collector = prometheus.Collector(options=options, view_data=view_data)
        self.assertEqual(options, collector.options)
        self.assertEqual(view_data, collector.view_data)
        self.assertEqual({}, collector.registered_views)
        self.assertEqual(registry, collector.registry)

    def test_collector_register_view(self):
        registry = mock.Mock()
        view_data = mock.Mock()
        options = prometheus.Options("test1", 8001, "localhost", registry)
        collector = prometheus.Collector(options=options, view_data=view_data)
        collector.register_view(VIDEO_SIZE_VIEW)
        collector.collect()

        self.assertEqual(REGISTERED_VIEW, collector.registered_views)

    def test_collector_add_view_data(self):
        registry = mock.Mock()
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        view_data = view_data_module.ViewData(
            view=VIDEO_SIZE_VIEW, start_time=start_time, end_time=end_time)
        options = prometheus.Options("test1", 8001, "localhost", registry)
        collector = prometheus.Collector(options=options, view_data={})
        collector.register_view(VIDEO_SIZE_VIEW)
        collector.add_view_data(view_data)
        v_data = {list(REGISTERED_VIEW)[0]: view_data}
        collector.collect()
        self.assertEqual(v_data, collector.view_data)

    def test_collector_to_metric_count(self):
        agg = aggregation_module.CountAggregation(256)
        view = view_module.View(VIDEO_SIZE_VIEW_NAME,
                                "processed video size over time",
                                [FRONTEND_KEY], VIDEO_SIZE_MEASURE, agg)
        registry = mock.Mock()
        view_data = mock.Mock()
        options = prometheus.Options("test1", 8001, "localhost", registry)
        collector = prometheus.Collector(options=options, view_data=view_data)
        collector.register_view(view)
        desc = collector.registered_views[list(REGISTERED_VIEW)[0]]
        metric = collector.to_metric(desc=desc, view=view)

        self.assertEqual(desc['name'], metric.name)
        self.assertEqual(desc['documentation'], metric.documentation)
        self.assertEqual('counter', metric.type)
        self.assertEqual(1, len(metric.samples))

    def test_collector_to_metric_sum(self):
        agg = aggregation_module.SumAggregation(256.0)
        view = view_module.View(VIDEO_SIZE_VIEW_NAME,
                                "processed video size over time",
                                [FRONTEND_KEY], VIDEO_SIZE_MEASURE, agg)
        registry = mock.Mock()
        view_data = mock.Mock()
        options = prometheus.Options("test1", 8001, "localhost", registry)
        collector = prometheus.Collector(options=options, view_data=view_data)
        collector.register_view(view)
        desc = collector.registered_views[list(REGISTERED_VIEW)[0]]
        metric = collector.to_metric(desc=desc, view=view)

        self.assertEqual(desc['name'], metric.name)
        self.assertEqual(desc['documentation'], metric.documentation)
        self.assertEqual('untyped', metric.type)
        self.assertEqual(1, len(metric.samples))

    def test_collector_to_metric_last_value(self):
        agg = aggregation_module.LastValueAggregation(256)
        view = view_module.View(VIDEO_SIZE_VIEW_NAME,
                                "processed video size over time",
                                [FRONTEND_KEY], VIDEO_SIZE_MEASURE, agg)
        registry = mock.Mock()
        view_data = mock.Mock()
        options = prometheus.Options("test1", 8001, "localhost", registry)
        collector = prometheus.Collector(options=options, view_data=view_data)
        collector.register_view(view)
        desc = collector.registered_views[list(REGISTERED_VIEW)[0]]
        metric = collector.to_metric(desc=desc, view=view)

        self.assertEqual(desc['name'], metric.name)
        self.assertEqual(desc['documentation'], metric.documentation)
        self.assertEqual('gauge', metric.type)
        self.assertEqual(1, len(metric.samples))

    def test_collector_to_metric_histogram(self):
        registry = mock.Mock()
        view_data = mock.Mock()
        options = prometheus.Options("test1", 8001, "localhost", registry)
        collector = prometheus.Collector(options=options, view_data=view_data)
        collector.register_view(VIDEO_SIZE_VIEW)
        desc = collector.registered_views[list(REGISTERED_VIEW)[0]]
        metric = collector.to_metric(desc=desc, view=VIDEO_SIZE_VIEW)

        self.assertEqual(desc['name'], metric.name)
        self.assertEqual(desc['documentation'], metric.documentation)
        self.assertEqual('histogram', metric.type)
        self.assertEqual(5, len(metric.samples))

    def test_collector_to_metric_invalid_dist(self):
        agg = mock.Mock()
        view = view_module.View(VIDEO_SIZE_VIEW_NAME,
                                "processed video size over time",
                                [FRONTEND_KEY], VIDEO_SIZE_MEASURE, agg)
        registry = mock.Mock()
        view_data = mock.Mock()
        options = prometheus.Options("test1", 8001, "localhost", registry)
        collector = prometheus.Collector(options=options, view_data=view_data)
        collector.register_view(view)
        desc = collector.registered_views[list(REGISTERED_VIEW)[0]]

        with self.assertRaisesRegexp(
                ValueError,
                'unsupported aggregation type <class \'mock.mock.Mock\'>'):
            collector.to_metric(desc=desc, view=view)

    def test_collector_collect(self):
        agg = aggregation_module.LastValueAggregation(256)
        view = view_module.View("new_view", "processed video size over time",
                                [FRONTEND_KEY], VIDEO_SIZE_MEASURE, agg)
        registry = mock.Mock()
        view_data = mock.Mock()
        options = prometheus.Options("test2", 8001, "localhost", registry)
        collector = prometheus.Collector(options=options, view_data=view_data)
        collector.register_view(view)
        desc = collector.registered_views[
            'test2_new_view-my.org/keys/frontend']
        collector.to_metric(desc=desc, view=view)

        registry = mock.Mock()
        view_data = mock.Mock()
        options = prometheus.Options("test1", 8001, "localhost", registry)
        collector = prometheus.Collector(options=options, view_data=view_data)
        collector.register_view(VIDEO_SIZE_VIEW)
        desc = collector.registered_views[list(REGISTERED_VIEW)[0]]
        metric = collector.to_metric(desc=desc, view=VIDEO_SIZE_VIEW)

        self.assertEqual(desc['name'], metric.name)
        self.assertEqual(desc['documentation'], metric.documentation)
        self.assertEqual('histogram', metric.type)
        self.assertEqual(5, len(metric.samples))


class TestPrometheusStatsExporter(unittest.TestCase):
    def test_exporter_constructor_no_namespace(self):
        with self.assertRaisesRegexp(ValueError,
                                     'Namespace can not be empty string.'):
            prometheus.new_stats_exporter(prometheus.Options())

    def test_emit(self):
        options = prometheus.Options(namespace="opencensus", port=9005)
        stats = stats_module.Stats()
        view_manager = stats.view_manager
        stats_recorder = stats.stats_recorder
        exporter = prometheus.new_stats_exporter(options)
        view_manager.register_exporter(exporter)
        view_manager.register_view(VIDEO_SIZE_VIEW)
        tag_value = tag_value_module.TagValue(str(1000))
        tag_map = tag_map_module.TagMap()
        tag_map.insert(FRONTEND_KEY, tag_value)
        measure_map = stats_recorder.new_measurement_map()
        measure_map.measure_int_put(VIDEO_SIZE_MEASURE, 25 * MiB)
        measure_map.record(tag_map)
        exporter.export([
            exporter.collector.view_data[(
                'opencensus_my.org/views/video_size_test2-my.org'
                '/keys/frontend')]
        ])

        self.assertIsInstance(
            exporter.collector.view_data[(
                'opencensus_my.org/views/video_size_test2-my.org'
                '/keys/frontend')], view_data_module.ViewData)
        self.assertEqual(REGISTERED_VIEW2, exporter.collector.registered_views)
        self.assertEqual(options, exporter.options)
        self.assertEqual(options.registry, exporter.gatherer)
        self.assertIsNotNone(exporter.collector)
        self.assertIsNotNone(exporter.transport)

    def test_tag_keys_to_labels(self):
        tags = ['One', 'Two', 'Three']
        labels = prometheus.tag_keys_to_labels(tags)
        self.assertEqual(tags, labels)

    def test_view_name(self):
        view_name = prometheus.view_name(
            namespace="opencensus", view=VIDEO_SIZE_VIEW)
        self.assertEqual("opencensus_my.org/views/video_size_test2", view_name)

    def test_view_name_without_namespace(self):
        view_name = prometheus.view_name(namespace="", view=VIDEO_SIZE_VIEW)
        self.assertEqual("my.org/views/video_size_test2", view_name)

    def test_view_signature(self):
        view_signature = prometheus.view_signature(
            namespace="", view=VIDEO_SIZE_VIEW)
        self.assertEqual("my.org/views/video_size_test2-my.org/keys/frontend",
                         view_signature)
