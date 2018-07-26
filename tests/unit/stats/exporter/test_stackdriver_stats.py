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

from opencensus.stats.exporters import stackdriver_exporter as stackdriver
from opencensus.stats import stats as stats_module

class TestStackdriverStatsExporter(unittest.TestCase):

	def test_constructor(self):
		exporter = stackdriver.StackdriverStatsExporter()

		self.assertEqual(exporter.client, None)
	
	def test_constructor_param(self):
		exporter = stackdriver.StackdriverStatsExporter(options = stackdriver.Options(project_id=1))
		
		self.assertEqual(exporter.options.project_id,1)

	def test_blank_project(self):
		self.assertRaises(Exception, stackdriver.new_stats_exporter, stackdriver.Options(project_id=""))

	def test_not_blank_project(self):
		exporter_created = stackdriver.new_stats_exporter(stackdriver.Options(project_id=1))

		self.assertIsInstance(exporter_created, stackdriver.StackdriverStatsExporter)

	def test_namespacedviews(self):
		view_name = "view-1"
		expected_view_name_namespaced = "custom.googleapis.com/opencensus/%s" % view_name
		view_name_namespaced = stackdriver.namespaced_view_name(view_name)
		
		self.assertEqual(expected_view_name_namespaced, view_name_namespaced)

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
