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
from datetime import datetime
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats.exporters import stackdriver_exporter as stackdriver
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.stats import view_data as view_data_module
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
VIDEO_SIZE_VIEW = view_module.View(VIDEO_SIZE_VIEW_NAME,
								"processed video size over time",
								[FRONTEND_KEY],
								VIDEO_SIZE_MEASURE,
								VIDEO_SIZE_DISTRIBUTION)

class TestOptions(unittest.TestCase):

	def test_options_blank(self):
		option = stackdriver.Options()

		self.assertEqual(option.project_id, "")
		self.assertEqual(option.resource, None)

	def test_options_parameters(self):
		option = stackdriver.Options(project_id="project-id", metric_prefix="sample")
		self.assertEqual(option.project_id, "project-id")
		self.assertEqual(option.metric_prefix, "sample")

	def test_default_monitoring_labels_blank(self):
		option = stackdriver.Options()
		self.assertEqual(option.default_monitoring_labels, None)

	def test_default_monitoring_labels(self):
		default_labels = {'key1':'value1'}
		option = stackdriver.Options(default_monitoring_labels=default_labels)
		self.assertEqual(option.default_monitoring_labels, default_labels)


class TestStackdriverStatsExporter(unittest.TestCase):

	def test_constructor(self):
		exporter = stackdriver.StackdriverStatsExporter()

		self.assertEqual(exporter.client, None)

	def test_constructor_param(self):
		project_id = 1
		default_labels = {'key1':'value1'}
		exporter = stackdriver.StackdriverStatsExporter(
								options=stackdriver.Options(project_id=project_id),
								default_labels=default_labels)

		self.assertEqual(exporter.options.project_id,project_id)
		self.assertEqual(exporter.default_labels,default_labels)

	def test_blank_project(self):
		self.assertRaises(Exception, stackdriver.new_stats_exporter, stackdriver.Options(project_id=""))

	def test_not_blank_project(self):
		exporter_created = stackdriver.new_stats_exporter(stackdriver.Options(project_id=1))

		self.assertIsInstance(exporter_created, stackdriver.StackdriverStatsExporter)

	def test_get_task_value(self):
		task_value = stackdriver.get_task_value()
		self.assertNotEqual(task_value, "")

	def test_new_label_descriptors(self):
		defaults = {'key1':'value1'}
		keys = [FRONTEND_KEY]
		output = stackdriver.new_label_descriptors(defaults,keys)
		self.assertEqual(len(output),2)

	def test_namespacedviews(self):
		view_name = "view-1"
		expected_view_name_namespaced = "custom.googleapis.com/opencensus/%s" % view_name
		view_name_namespaced = stackdriver.namespaced_view_name(view_name)

		self.assertEqual(expected_view_name_namespaced, view_name_namespaced)

	def test_get_task_value(self):
		task_value = stackdriver.get_task_value()

		self.assertNotEqual(task_value, "")

	def test_on_register_view(self):
		client = mock.Mock()
		option = stackdriver.Options(project_id="project-test")
		exporter = stackdriver.StackdriverStatsExporter(options=option, client=client)
		exporter.on_register_view(VIDEO_SIZE_VIEW)
		self.assertTrue(True)

	def test_emit(self):
		client = mock.Mock()
		start_time = datetime.utcnow()
		end_time = datetime.utcnow()
		v_data = view_data_module.ViewData(view=VIDEO_SIZE_VIEW,
											  start_time=start_time,
											  end_time=end_time)
		view_data = [v_data]
		option = stackdriver.Options(project_id="project-test")
		exporter = stackdriver.StackdriverStatsExporter(options=option, client=client)
		exporter.export(view_data)
		self.assertTrue(True)

	def test_export(self):
		client = mock.Mock()
		start_time = datetime.utcnow()
		end_time = datetime.utcnow()
		v_data = view_data_module.ViewData(view=VIDEO_SIZE_VIEW,
											  start_time=start_time,
											  end_time=end_time)
		view_data = [v_data]
		option = stackdriver.Options(project_id="project-test")
		exporter = stackdriver.StackdriverStatsExporter(options=option, client=client)
		exporter.export(view_data)
		self.assertTrue(True)

	def test_handle_upload(self):
		client = mock.Mock()
		start_time = datetime.utcnow()
		end_time = datetime.utcnow()
		v_data = view_data_module.ViewData(view=VIDEO_SIZE_VIEW,
											  start_time=start_time,
											  end_time=end_time)
		view_data = [v_data]
		option = stackdriver.Options(project_id="project-test")
		exporter = stackdriver.StackdriverStatsExporter(options=option, client=client)
		exporter.export(view_data)
		self.assertTrue(True)

	def test_make_request(self):
		client = mock.Mock()
		start_time = datetime.utcnow()
		end_time = datetime.utcnow()
		v_data = view_data_module.ViewData(view=VIDEO_SIZE_VIEW,
											  start_time=start_time,
											  end_time=end_time)
		view_data = [v_data]
		option = stackdriver.Options(project_id="project-test")
		exporter = stackdriver.StackdriverStatsExporter(options=option, client=client)
		requests = exporter.make_request(view_data,1)
		self.assertEqual(len(requests), 1)

	def test_create_timeseries(self):
		client = mock.Mock()
		start_time = datetime.utcnow()
		end_time = datetime.utcnow()
		v_data = view_data_module.ViewData(view=VIDEO_SIZE_VIEW,
											  start_time=start_time,
											  end_time=end_time)
		option = stackdriver.Options(project_id="project-test")
		exporter = stackdriver.StackdriverStatsExporter(options=option, client=client)
		time_serie = exporter.create_time_series_list(v_data,None)
		self.assertIsNotNone(time_serie)

	def test_create_metric_descriptor(self):
		client = mock.Mock()
		start_time = datetime.utcnow()
		end_time = datetime.utcnow()
		option = stackdriver.Options(project_id="project-test")
		exporter = stackdriver.StackdriverStatsExporter(options=option, client=client)
		exporter.create_metric_descriptor(VIDEO_SIZE_VIEW)
		self.assertTrue(True)

	def test_stackdriver_register_exporter(self):
		view = mock.Mock()
		stats = stats_module.Stats()
		view_manager = stats.view_manager
		stats_recorder = stats.stats_recorder

		exporter = mock.Mock()
		view_manager.register_exporter(exporter)

		registered_exporters = len(view_manager.measure_to_view_map.exporters)

		self.assertEqual(registered_exporters, 1)
