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

import unittest
import mock

from opencensus.stats.exporters import prometheus_exporter as prometheus
from opencensus.stats import stats as stats_module


class TestOptionsPrometheus(unittest.TestCase):

    def test_options_constructor(self):
        option = prometheus.Options("test1")
        self.assertEqual(option.namespace, "test1")

    def test_options_constructor_with_params(self):
        registry = mock.Mock()
        option = prometheus.Options("test1",8001,"localhost",registry)
        self.assertEqual(option.namespace, "test1")
        self.assertEqual(option.port,8001)
        self.assertEqual(option.address,"localhost")
        self.assertEqual(option.registry, registry)


class TestCollectorPrometheus(unittest.TestCase):

    def test_collector_constructor(self):
        options = prometheus.Options("test1")
        collector = prometheus.Collector(options)
        self.assertEqual(collector.options, options)

    def test_collector_constructor_with_param(self):
        options = prometheus.Options("test1")
        view_data = {'key1': 'value1'}
        collector = prometheus.Collector(options,view_data)
        self.assertEqual(collector.options, options)
        self.assertEqual(collector.view_data, view_data)
        self.assertEqual(collector.registry, options.registry)
        self.assertEqual(collector.registered_views, {})


class TestPrometheusStatsExporter(unittest.TestCase):

    def test_constructor(self):
        exporter = prometheus.PrometheusStatsExporter()

        self.assertIsInstance(exporter, prometheus.PrometheusStatsExporter)
    
    def test_constructor_param(self):
        exporter = prometheus.PrometheusStatsExporter(
            options = prometheus.Options(namespace="example"))
        
        self.assertEqual(exporter.options.namespace,"example")

    def test_blank_project(self):
        self.assertRaises(ValueError, prometheus.new_stats_exporter, prometheus.Options(namespace=""))

    def test_not_blank_project(self):
        exporter_created = prometheus.new_stats_exporter(
            prometheus.Options(namespace="example"))

        self.assertIsInstance(exporter_created, prometheus.PrometheusStatsExporter)

    def test_new_collector(self):
        collector = prometheus.new_collector(prometheus.Options(namespace="test-collector"))
        self.assertEqual(collector, prometheus.Collector)

    def test_get_task_value(self):
        task_value = stackdriver.get_task_value()

        self.assertNotEqual(task_value, "")

    def test_stackdriver_register_exporter(self):
        view = mock.Mock()
        stats = stats_module.Stats()
        view_manager = stats.view_manager
        stats_recorder = stats.stats_recorder

        exporter = mock.Mock()
        view_manager.register_exporter(exporter)

        registered_exporters = len(view_manager.measure_to_view_map.exporters)

        self.assertEqual(registered_exporters, 1)
