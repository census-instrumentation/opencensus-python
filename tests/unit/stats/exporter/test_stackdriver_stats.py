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
FRONTEND_KEY_FLOAT = tag_key_module.TagKey("my.org/keys/frontend-FLOAT")
FRONTEND_KEY_INT = tag_key_module.TagKey("my.org/keys/frontend-INT")
FRONTEND_KEY_STR = tag_key_module.TagKey("my.org/keys/frontend-INT")

VIDEO_SIZE_MEASURE = measure_module.MeasureInt(
    "my.org/measure/video_size_test2", "size of processed videos", "By")

VIDEO_SIZE_MEASURE_FLOAT = measure_module.MeasureFloat(
    "my.org/measure/video_size_test-float", "size of processed videos-float", "By")

VIDEO_SIZE_VIEW_NAME = "my.org/views/video_size_test2"
VIDEO_SIZE_DISTRIBUTION = aggregation_module.DistributionAggregation(
                            [0.0, 16.0 * MiB, 256.0 * MiB])
VIDEO_SIZE_VIEW = view_module.View(VIDEO_SIZE_VIEW_NAME,
                                "processed video size over time",
                                [FRONTEND_KEY],
                                VIDEO_SIZE_MEASURE,
                                VIDEO_SIZE_DISTRIBUTION)


class _Client(object):
    def __init__(self, project=None):
        if project is None:
            project = 'PROJECT'

        self.project = project


class TestOptions(unittest.TestCase):

    def test_options_blank(self):
        option = stackdriver.Options()

        self.assertEqual(option.project_id, "")
        self.assertEqual(option.resource, "")

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
        patch_client = mock.patch(
            'opencensus.stats.exporters.stackdriver_exporter.monitoring_v3.MetricServiceClient', _Client)

        with patch_client:
            exporter_created = stackdriver.new_stats_exporter(stackdriver.Options(project_id=1))

        self.assertIsInstance(exporter_created, stackdriver.StackdriverStatsExporter)

    def test_as_float(self):
        value = 1.5
        result = stackdriver.as_float(value)
        self.assertEqual(result[0], value)
        self.assertEqual(result[1], True)

    def test_is_not_float(self):
        value = "a*7"
        result = stackdriver.as_float(value)
        self.assertEqual(result[0], None)
        self.assertEqual(result[1], False)

    def test_remove_invalid_chars(self):
        invalid_chars = "@#$"
        valid_chars = "abc"

        result = stackdriver.remove_non_alphanumeric(invalid_chars)
        self.assertEqual(result, "")

        result = stackdriver.remove_non_alphanumeric(valid_chars)
        self.assertEqual(result, "abc")

    def test_singleton_with_params(self):
        default_labels = {'key1':'value1'}
        patch_client = mock.patch(
            'opencensus.stats.exporters.stackdriver_exporter.monitoring_v3.MetricServiceClient',
            _Client)

        with patch_client:
            exporter_created = stackdriver.new_stats_exporter(stackdriver.Options(project_id=1,default_monitoring_labels=default_labels))

        self.assertEqual(exporter_created.default_labels, default_labels)

    def test_get_task_value(self):
        task_value = stackdriver.get_task_value()
        self.assertNotEqual(task_value, "")

    def test_set_default_labels(self):
        labels = {'key':'value'}
        exporter = stackdriver.StackdriverStatsExporter()
        exporter.set_default_labels(labels)
        self.assertEqual(exporter.default_labels, labels)

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
        view_none = None
        option = stackdriver.Options(project_id="project-test")
        exporter = stackdriver.StackdriverStatsExporter(options=option, client=client)
        exporter.on_register_view(VIDEO_SIZE_VIEW)
        self.assertTrue(True)
        exporter.on_register_view(view_none)
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
        exporter.emit(view_data)
        self.assertTrue(True)
        exporter.emit(None)
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
        exporter.export(None)
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
        exporter.handle_upload(view_data)
        self.assertTrue(True)
        exporter.handle_upload(None)
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

    def test_stackdriver_register_exporter(self):
        view = mock.Mock()
        stats = stats_module.Stats()
        view_manager = stats.view_manager
        stats_recorder = stats.stats_recorder

        exporter = mock.Mock()
        if len(view_manager.measure_to_view_map.exporters) > 0:
            view_manager.unregister_exporter(view_manager.measure_to_view_map.exporters[0])
        view_manager.register_exporter(exporter)

        registered_exporters = len(view_manager.measure_to_view_map.exporters)

        self.assertEqual(registered_exporters, 1)

    def test_create_timeseries(self):
        client = mock.Mock()
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()

        option = stackdriver.Options(project_id="project-test", resource="global")
        exporter = stackdriver.StackdriverStatsExporter(options=option, client=client)

        stats = stats_module.Stats()
        view_manager = stats.view_manager
        stats_recorder = stats.stats_recorder

        if len(view_manager.measure_to_view_map.exporters) > 0:
            view_manager.unregister_exporter(view_manager.measure_to_view_map.exporters[0])

        view_manager.register_exporter(exporter)

        view_manager.register_view(VIDEO_SIZE_VIEW)

        tag_value = tag_value_module.TagValue("1200")
        tag_map = tag_map_module.TagMap()
        tag_map.insert(FRONTEND_KEY, tag_value)
        measure_map = stats_recorder.new_measurement_map()
        measure_map.measure_int_put(VIDEO_SIZE_MEASURE, 25 * MiB)

        measure_map.record(tag_map)

        v_data = measure_map.measure_to_view_map.get_view(VIDEO_SIZE_VIEW_NAME, None)

        time_serie = exporter.create_time_series_list(v_data,"")
        self.assertIsNotNone(time_serie)
        time_serie = exporter.create_time_series_list(v_data,"global")
        self.assertIsNotNone(time_serie)

    def test_create_timeseries_str_tagvalue(self):
        client = mock.Mock()
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()

        option = stackdriver.Options(project_id="project-test", resource="global")
        exporter = stackdriver.StackdriverStatsExporter(options=option, client=client)

        stats = stats_module.Stats()
        view_manager = stats.view_manager
        stats_recorder = stats.stats_recorder

        if len(view_manager.measure_to_view_map.exporters) > 0:
            view_manager.unregister_exporter(view_manager.measure_to_view_map.exporters[0])

        view_manager.register_exporter(exporter)

        agg_1 = aggregation_module.LastValueAggregation(value=2)
        view_name1 = "view-name1"
        new_view1 = view_module.View(view_name1,
                                "processed video size over time",
                                [FRONTEND_KEY_INT],
                                VIDEO_SIZE_MEASURE,
                                agg_1)

        view_manager.register_view(new_view1)

        tag_value_int = tag_value_module.TagValue("Abc")

        tag_map = tag_map_module.TagMap()

        tag_map.insert(FRONTEND_KEY_INT, tag_value_int)

        measure_map = stats_recorder.new_measurement_map()
        measure_map.measure_int_put(VIDEO_SIZE_MEASURE, 25 * MiB)

        measure_map.record(tag_map)

        v_data = measure_map.measure_to_view_map.get_view(view_name1, None)

        time_serie = exporter.create_time_series_list(v_data,"global")
        self.assertIsNotNone(time_serie)

    def test_create_timeseries_last_value_float_tagvalue(self):
        client = mock.Mock()
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()

        option = stackdriver.Options(project_id="project-test", resource="global")
        exporter = stackdriver.StackdriverStatsExporter(options=option, client=client)

        stats = stats_module.Stats()
        view_manager = stats.view_manager
        stats_recorder = stats.stats_recorder

        if len(view_manager.measure_to_view_map.exporters) > 0:
            view_manager.unregister_exporter(view_manager.measure_to_view_map.exporters[0])

        view_manager.register_exporter(exporter)

        agg_1 = aggregation_module.LastValueAggregation(value=2)
        view_name1 = "view-name1"
        new_view1 = view_module.View(view_name1,
                                "processed video size over time",
                                [FRONTEND_KEY_FLOAT],
                                VIDEO_SIZE_MEASURE_FLOAT,
                                agg_1)

        view_manager.register_view(new_view1)

        tag_value_int = tag_value_module.TagValue("Abc")

        tag_map = tag_map_module.TagMap()

        tag_map.insert(FRONTEND_KEY_INT, tag_value_int)

        measure_map = stats_recorder.new_measurement_map()
        measure_map.measure_int_put(VIDEO_SIZE_MEASURE, 25 * MiB)

        measure_map.record(tag_map)

        v_data = measure_map.measure_to_view_map.get_view(view_name1, None)

        time_serie = exporter.create_time_series_list(v_data,"global")
        self.assertIsNotNone(time_serie)

    def test_create_timeseries_float_tagvalue(self):
        client = mock.Mock()
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()

        option = stackdriver.Options(project_id="project-test", resource="global")
        exporter = stackdriver.StackdriverStatsExporter(options=option, client=client)

        stats = stats_module.Stats()
        view_manager = stats.view_manager
        stats_recorder = stats.stats_recorder

        if len(view_manager.measure_to_view_map.exporters) > 0:
            view_manager.unregister_exporter(view_manager.measure_to_view_map.exporters[0])

        view_manager.register_exporter(exporter)

        agg_2 = aggregation_module.SumAggregation(sum=2.2)
        view_name2 = "view-name2"
        new_view2 = view_module.View(view_name2,
                                "processed video size over time",
                                [FRONTEND_KEY_FLOAT],
                                VIDEO_SIZE_MEASURE_FLOAT,
                                agg_2)

        view_manager.register_view(new_view2)

        tag_value_float = tag_value_module.TagValue("1200")

        tag_map = tag_map_module.TagMap()

        tag_map.insert(FRONTEND_KEY_FLOAT, tag_value_float)

        measure_map = stats_recorder.new_measurement_map()
        measure_map.measure_float_put(VIDEO_SIZE_MEASURE_FLOAT, 25 * MiB)

        measure_map.record(tag_map)

        v_data = measure_map.measure_to_view_map.get_view(view_name2, None)

        time_serie = exporter.create_time_series_list(v_data,"global")
        self.assertIsNotNone(time_serie)

    def test_create_metric_descriptor_count(self):
        client = mock.Mock()
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        option = stackdriver.Options(project_id="project-test", metric_prefix="teste")
        view_name_count= "view-count"
        agg_count = aggregation_module.CountAggregation(count=2)
        view_count = view_module.View(view_name_count,
                                        "processed video size over time",
                                        [FRONTEND_KEY],
                                        VIDEO_SIZE_MEASURE,
                                        agg_count)
        exporter = stackdriver.StackdriverStatsExporter(options=option, client=client)
        desc = exporter.create_metric_descriptor(view_count)
        self.assertNotEqual(desc, None)

    def test_create_metric_descriptor_sum_int(self):
        client = mock.Mock()
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        option = stackdriver.Options(project_id="project-test", metric_prefix="teste")

        view_name_sum_int= "view-sum-int"
        agg_sum = aggregation_module.SumAggregation(sum=2)
        view_sum_int = view_module.View(view_name_sum_int,
                                        "processed video size over time",
                                        [FRONTEND_KEY],
                                        VIDEO_SIZE_MEASURE,
                                        agg_sum)
        exporter = stackdriver.StackdriverStatsExporter(options=option, client=client)
        desc = exporter.create_metric_descriptor(view_sum_int)
        self.assertNotEqual(desc, None)

    def test_create_metric_descriptor_sum_float(self):
        client = mock.Mock()
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        option = stackdriver.Options(project_id="project-test", metric_prefix="teste")

        view_name_sum_float= "view-sum-float"
        agg_sum = aggregation_module.SumAggregation(sum=2)
        view_sum_float = view_module.View(view_name_sum_float,
                                        "processed video size over time",
                                        [FRONTEND_KEY_FLOAT],
                                        VIDEO_SIZE_MEASURE_FLOAT,
                                        agg_sum)
        exporter = stackdriver.StackdriverStatsExporter(options=option, client=client)
        desc = exporter.create_metric_descriptor(view_sum_float)
        self.assertNotEqual(desc, None)

    def test_create_metric_descriptor(self):
        client = mock.Mock()
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        option = stackdriver.Options(project_id="project-test", metric_prefix="teste")
        exporter = stackdriver.StackdriverStatsExporter(options=option, client=client)
        desc = exporter.create_metric_descriptor(VIDEO_SIZE_VIEW)
        self.assertNotEqual(desc, None)


    def test_create_metric_descriptor_last_value_int(self):
        client = mock.Mock()
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        option = stackdriver.Options(project_id="project-test", metric_prefix="teste")

        view_name_base= "view-base"
        agg_base = aggregation_module.LastValueAggregation()
        view_base = view_module.View(view_name_base,
                                        "processed video size over time",
                                        [FRONTEND_KEY],
                                        VIDEO_SIZE_MEASURE,
                                        agg_base)
        exporter = stackdriver.StackdriverStatsExporter(options=option, client=client)
        desc = exporter.create_metric_descriptor(view_base)
        self.assertNotEqual(desc, None)

    def test_create_metric_descriptor_last_value_float(self):
        client = mock.Mock()
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        option = stackdriver.Options(project_id="project-test", metric_prefix="teste")

        view_name_base= "view-base"
        agg_base = aggregation_module.LastValueAggregation()
        view_base = view_module.View(view_name_base,
                                        "processed video size over time",
                                        [FRONTEND_KEY],
                                        VIDEO_SIZE_MEASURE_FLOAT,
                                        agg_base)
        exporter = stackdriver.StackdriverStatsExporter(options=option, client=client)
        desc = exporter.create_metric_descriptor(view_base)
        self.assertNotEqual(desc, None)

    def test_create_metric_descriptor_base(self):
        client = mock.Mock()
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        option = stackdriver.Options(project_id="project-test", metric_prefix="teste")

        view_name_base= "view-base"
        agg_base = aggregation_module.BaseAggregation()
        view_base = view_module.View(view_name_base,
                                        "processed video size over time",
                                        [FRONTEND_KEY],
                                        VIDEO_SIZE_MEASURE,
                                        agg_base)
        exporter = stackdriver.StackdriverStatsExporter(options=option, client=client)
        self.assertRaises(Exception, exporter.create_metric_descriptor, view_base)
