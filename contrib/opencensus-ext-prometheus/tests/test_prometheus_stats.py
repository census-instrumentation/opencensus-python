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
import copy
import mock
import unittest

from prometheus_client.core import Sample

from opencensus.ext.prometheus import stats_exporter as prometheus
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.stats import view_data as view_data_module
from opencensus.tags import tag_key as tag_key_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.tags import tag_value as tag_value_module

MiB = 1 << 20
FRONTEND_KEY = tag_key_module.TagKey("myorg_keys_frontend")
FRONTEND_KEY_FLOAT = tag_key_module.TagKey("myorg_keys_frontend_FLOAT")
FRONTEND_KEY_INT = tag_key_module.TagKey("myorg_keys_frontend_INT")
FRONTEND_KEY_STR = tag_key_module.TagKey("myorg_keys_frontend_INT")

VIDEO_SIZE_MEASURE = measure_module.MeasureInt(
    "myorg_measure_video_size_test2", "size of processed videos", "By")

VIDEO_SIZE_MEASURE_FLOAT = measure_module.MeasureFloat(
    "myorg_measure_video_size_test_float", "size of processed videos float",
    "By")

VIDEO_SIZE_VIEW_NAME = "myorg_views_video_size_test2"
VIDEO_SIZE_DISTRIBUTION = aggregation_module.DistributionAggregation(
    [16.0 * MiB, 256.0 * MiB])
VIDEO_SIZE_VIEW = view_module.View(
    VIDEO_SIZE_VIEW_NAME, "processed video size over time", [FRONTEND_KEY],
    VIDEO_SIZE_MEASURE, VIDEO_SIZE_DISTRIBUTION)
REGISTERED_VIEW = {
    'test1_myorg_views_video_size_test2': {
        'documentation': 'processed video size over time',
        'labels': ['myorg_keys_frontend'],
        'name': 'test1_myorg_views_video_size_test2'
    }
}

REGISTERED_VIEW2 = {
    'opencensus_myorg_views_video_size_test2': {
        'documentation': 'processed video size over time',
        'labels': ['myorg_keys_frontend'],
        'name': 'opencensus_myorg_views_video_size_test2'
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
        view_name_to_data_map = mock.Mock()
        options = prometheus.Options("test1", 8001, "localhost", registry)
        self.assertEqual(options.namespace, "test1")
        self.assertEqual(options.port, 8001)
        self.assertEqual(options.address, "localhost")
        self.assertEqual(options.registry, registry)

        collector = prometheus.Collector(
            options=options, view_name_to_data_map=view_name_to_data_map)
        self.assertEqual(options, collector.options)
        self.assertEqual(
            view_name_to_data_map, collector.view_name_to_data_map)
        self.assertEqual({}, collector.registered_views)
        self.assertEqual(registry, collector.registry)

    def test_collector_register_view(self):
        registry = mock.Mock()
        view_name_to_data_map = mock.Mock()
        options = prometheus.Options("test1", 8001, "localhost", registry)
        collector = prometheus.Collector(
            options=options, view_name_to_data_map=view_name_to_data_map)
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
        collector = prometheus.Collector(options=options)
        collector.register_view(VIDEO_SIZE_VIEW)
        collector.add_view_data(view_data)
        view_name_to_data_map = {list(REGISTERED_VIEW)[0]: view_data}
        collector.collect()
        self.assertEqual(
            view_name_to_data_map, collector.view_name_to_data_map)

    def test_collector_to_metric_count(self):
        agg = aggregation_module.CountAggregation(256)
        view = view_module.View(VIDEO_SIZE_VIEW_NAME,
                                "processed video size over time",
                                [FRONTEND_KEY], VIDEO_SIZE_MEASURE, agg)
        registry = mock.Mock()
        options = prometheus.Options("test1", 8001, "localhost", registry)
        collector = prometheus.Collector(options=options)
        collector.register_view(view)
        desc = collector.registered_views[list(REGISTERED_VIEW)[0]]
        metric = collector.to_metric(
            desc=desc, tag_values=[None], agg_data=agg.aggregation_data)

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
        options = prometheus.Options("test1", 8001, "localhost", registry)
        collector = prometheus.Collector(options=options)
        collector.register_view(view)
        desc = collector.registered_views[list(REGISTERED_VIEW)[0]]
        metric = collector.to_metric(
            desc=desc, tag_values=[None], agg_data=agg.aggregation_data)

        self.assertEqual(desc['name'], metric.name)
        self.assertEqual(desc['documentation'], metric.documentation)
        self.assertEqual('unknown', metric.type)
        self.assertEqual(1, len(metric.samples))

    def test_collector_to_metric_last_value(self):
        agg = aggregation_module.LastValueAggregation(256)
        view = view_module.View(VIDEO_SIZE_VIEW_NAME,
                                "processed video size over time",
                                [FRONTEND_KEY], VIDEO_SIZE_MEASURE, agg)
        registry = mock.Mock()
        options = prometheus.Options("test1", 8001, "localhost", registry)
        collector = prometheus.Collector(options=options)
        collector.register_view(view)
        desc = collector.registered_views[list(REGISTERED_VIEW)[0]]
        metric = collector.to_metric(
            desc=desc, tag_values=[None], agg_data=agg.aggregation_data)

        self.assertEqual(desc['name'], metric.name)
        self.assertEqual(desc['documentation'], metric.documentation)
        self.assertEqual('gauge', metric.type)
        self.assertEqual(1, len(metric.samples))

    def test_collector_to_metric_histogram(self):
        registry = mock.Mock()
        options = prometheus.Options("test1", 8001, "localhost", registry)
        collector = prometheus.Collector(options=options)
        collector.register_view(VIDEO_SIZE_VIEW)
        desc = collector.registered_views[list(REGISTERED_VIEW)[0]]
        distribution = copy.deepcopy(VIDEO_SIZE_DISTRIBUTION.aggregation_data)
        distribution.add_sample(280.0 * MiB, None, None)
        metric = collector.to_metric(
            desc=desc,
            tag_values=[tag_value_module.TagValue("ios")],
            agg_data=distribution)

        self.assertEqual(desc['name'], metric.name)
        self.assertEqual(desc['documentation'], metric.documentation)
        self.assertEqual('histogram', metric.type)
        expected_samples = [
            Sample(metric.name + '_bucket',
                   {"myorg_keys_frontend": "ios", "le": str(16.0 * MiB)},
                   0),
            Sample(metric.name + '_bucket',
                   {"myorg_keys_frontend": "ios", "le": str(256.0 * MiB)},
                   0),
            Sample(metric.name + '_bucket',
                   {"myorg_keys_frontend": "ios", "le": "+Inf"},
                   1),
            Sample(metric.name + '_count', {"myorg_keys_frontend": "ios"}, 1),
            Sample(metric.name + '_sum',
                   {"myorg_keys_frontend": "ios"},
                   280.0 * MiB)]
        self.assertEqual(expected_samples, metric.samples)

    def test_collector_to_metric_invalid_dist(self):
        agg = mock.Mock()
        view = view_module.View(VIDEO_SIZE_VIEW_NAME,
                                "processed video size over time",
                                [FRONTEND_KEY], VIDEO_SIZE_MEASURE, agg)
        registry = mock.Mock()
        options = prometheus.Options("test1", 8001, "localhost", registry)
        collector = prometheus.Collector(options=options)
        collector.register_view(view)
        desc = collector.registered_views[list(REGISTERED_VIEW)[0]]

        with self.assertRaisesRegexp(
                ValueError,
                'unsupported aggregation type <class \'mock.mock.Mock\'>'):
            collector.to_metric(desc=desc, tag_values=[None], agg_data=agg)

    def test_collector_collect(self):
        agg = aggregation_module.LastValueAggregation(256)
        view = view_module.View("new_view", "processed video size over time",
                                [FRONTEND_KEY], VIDEO_SIZE_MEASURE, agg)
        registry = mock.Mock()
        options = prometheus.Options("test2", 8001, "localhost", registry)
        collector = prometheus.Collector(options=options)
        collector.register_view(view)
        desc = collector.registered_views['test2_new_view']
        metric = collector.to_metric(
            desc=desc,
            tag_values=[tag_value_module.TagValue("value")],
            agg_data=agg.aggregation_data)

        self.assertEqual(desc['name'], metric.name)
        self.assertEqual(desc['documentation'], metric.documentation)
        self.assertEqual('gauge', metric.type)
        expected_samples = [
            Sample(metric.name, {"myorg_keys_frontend": "value"}, 256)]
        self.assertEqual(expected_samples, metric.samples)

    def test_collector_collect_with_none_label_value(self):
        agg = aggregation_module.LastValueAggregation(256)
        view = view_module.View("new_view", "processed video size over time",
                                [FRONTEND_KEY], VIDEO_SIZE_MEASURE, agg)
        registry = mock.Mock()
        options = prometheus.Options("test3", 8001, "localhost", registry)
        collector = prometheus.Collector(options=options)
        collector.register_view(view)
        desc = collector.registered_views['test3_new_view']
        metric = collector.to_metric(
            desc=desc, tag_values=[None], agg_data=agg.aggregation_data)

        self.assertEqual(1, len(metric.samples))
        sample = metric.samples[0]
        # Sample is a namedtuple
        # ('Sample', ['name', 'labels', 'value', 'timestamp', 'exemplar'])
        label_map = sample[1]
        self.assertEqual({"myorg_keys_frontend": ""}, label_map)


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
            exporter.collector.view_name_to_data_map[
                'opencensus_myorg_views_video_size_test2']])

        self.assertIsInstance(
            exporter.collector.view_name_to_data_map[
                'opencensus_myorg_views_video_size_test2'],
            view_data_module.ViewData)
        self.assertEqual(REGISTERED_VIEW2, exporter.collector.registered_views)
        self.assertEqual(options, exporter.options)
        self.assertEqual(options.registry, exporter.gatherer)
        self.assertIsNotNone(exporter.collector)
        self.assertIsNotNone(exporter.transport)

    def test_get_view_name(self):
        v_name = prometheus.get_view_name(
            namespace="opencensus", view=VIDEO_SIZE_VIEW)
        self.assertEqual("opencensus_myorg_views_video_size_test2", v_name)

    def test_get_view_name_without_namespace(self):
        v_name = prometheus.get_view_name(namespace="", view=VIDEO_SIZE_VIEW)
        self.assertEqual("myorg_views_video_size_test2", v_name)

    def test_sanitize(self):
        v_name = prometheus.sanitize("demo/latency")
        self.assertEqual("demo_latency", v_name)
        label_name = prometheus.sanitize("my.org/demo/key1")
        self.assertEqual("my_org_demo_key1", label_name)
