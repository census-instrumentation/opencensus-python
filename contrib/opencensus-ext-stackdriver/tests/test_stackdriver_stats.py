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

from google.cloud import monitoring_v3

from opencensus.common import utils
from opencensus.common.version import __version__
from opencensus.ext.stackdriver import stats_exporter as stackdriver
from opencensus.metrics import label_key
from opencensus.metrics import label_value
from opencensus.metrics import transport as transport_module
from opencensus.metrics.export import metric
from opencensus.metrics.export import metric_descriptor
from opencensus.metrics.export import point
from opencensus.metrics.export import time_series
from opencensus.metrics.export import value
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import aggregation_data as aggregation_data_module
from opencensus.stats import execution_context
from opencensus.stats import measure as measure_module
from opencensus.stats import metric_utils
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
FRONTEND_KEY_STR = tag_key_module.TagKey("my.org/keys/frontend-STR")

FRONTEND_KEY_CLEAN = "my_org_keys_frontend"
FRONTEND_KEY_FLOAT_CLEAN = "my_org_keys_frontend_FLOAT"
FRONTEND_KEY_INT_CLEAN = "my_org_keys_frontend_INT"
FRONTEND_KEY_STR_CLEAN = "my_org_keys_frontend_STR"

VIDEO_SIZE_MEASURE = measure_module.MeasureFloat(
    "my.org/measure/video_size_test2", "size of processed videos", "By")
VIDEO_SIZE_MEASURE_2 = measure_module.MeasureFloat(
    "my.org/measure/video_size_test_2", "size of processed videos", "By")

VIDEO_SIZE_MEASURE_FLOAT = measure_module.MeasureFloat(
    "my.org/measure/video_size_test-float", "size of processed videos-float",
    "By")

VIDEO_SIZE_VIEW_NAME = "my.org/views/video_size_test2"
VIDEO_SIZE_DISTRIBUTION = aggregation_module.DistributionAggregation(
    [16.0 * MiB, 256.0 * MiB])
VIDEO_SIZE_VIEW = view_module.View(
    VIDEO_SIZE_VIEW_NAME, "processed video size over time", [FRONTEND_KEY],
    VIDEO_SIZE_MEASURE, VIDEO_SIZE_DISTRIBUTION)

TEST_TIME = datetime(2018, 12, 25, 1, 2, 3, 4)
TEST_TIME_STR = utils.to_iso_str(TEST_TIME)


class _Client(object):
    def __init__(self, client_info=None):
        self.client_info = client_info


class TestOptions(unittest.TestCase):
    def test_options_blank(self):
        option = stackdriver.Options()

        self.assertEqual(option.project_id, "")
        self.assertEqual(option.resource, "")

    def test_options_parameters(self):
        option = stackdriver.Options(
            project_id="project-id", metric_prefix="sample")
        self.assertEqual(option.project_id, "project-id")
        self.assertEqual(option.metric_prefix, "sample")

    def test_default_monitoring_labels_blank(self):
        option = stackdriver.Options()
        self.assertIsNone(option.default_monitoring_labels)

    def test_default_monitoring_labels(self):
        default_labels = {'key1': 'value1'}
        option = stackdriver.Options(default_monitoring_labels=default_labels)
        self.assertEqual(option.default_monitoring_labels, default_labels)


class TestStackdriverStatsExporter(unittest.TestCase):
    def test_constructor(self):
        exporter = stackdriver.StackdriverStatsExporter()

        self.assertIsNone(exporter.client)

    def test_constructor_param(self):
        project_id = 1
        default_labels = {'key1': 'value1'}
        exporter = stackdriver.StackdriverStatsExporter(
            options=stackdriver.Options(
                project_id=project_id,
                default_monitoring_labels=default_labels))
        self.assertEqual(exporter.options.project_id, project_id)

    def test_blank_project(self):
        self.assertRaises(ValueError, stackdriver.new_stats_exporter,
                          stackdriver.Options(project_id=""))

    def test_not_blank_project(self):
        patch_client = mock.patch(
            ('opencensus.ext.stackdriver.stats_exporter'
             '.monitoring_v3.MetricServiceClient'), _Client)

        with patch_client:
            exporter_created, transport = stackdriver.new_stats_exporter(
                stackdriver.Options(project_id=1))

        self.assertIsInstance(exporter_created,
                              stackdriver.StackdriverStatsExporter)

    def test_get_user_agent_slug(self):
        self.assertIn(__version__, stackdriver.get_user_agent_slug())

    def test_client_info_user_agent(self):
        """Check that the monitoring client sets a user agent.

        The user agent should include the library version. Note that this
        assumes MetricServiceClient calls ClientInfo.to_user_agent to attach
        the user agent as metadata to metric service API calls.
        """
        patch_client = mock.patch(
            'opencensus.ext.stackdriver.stats_exporter.monitoring_v3'
            '.MetricServiceClient', _Client)

        with patch_client:
            exporter, transport = stackdriver.new_stats_exporter(
                stackdriver.Options(project_id=1))

        self.assertIn(stackdriver.get_user_agent_slug(),
                      exporter.client.client_info.to_user_agent())

    def test_sanitize(self):
        # empty
        result = stackdriver.sanitize_label("")
        self.assertEqual(result, "")

        # all invalid
        result = stackdriver.sanitize_label("/*^#$")
        self.assertEqual(result, "key_")

        # all valid
        result = stackdriver.sanitize_label("abc")
        self.assertEqual(result, "abc")

        # mixed
        result = stackdriver.sanitize_label("a.b/c")
        self.assertEqual(result, "a_b_c")

        # starts with '_'
        result = stackdriver.sanitize_label("_abc")
        self.assertEqual(result, "key_abc")

        # starts with digit
        result = stackdriver.sanitize_label("0abc")
        self.assertEqual(result, "key_0abc")

        # too long
        result = stackdriver.sanitize_label("0123456789" * 10)
        self.assertEqual(len(result), 100)
        self.assertEqual(result, "key_" + "0123456789" * 9 + "012345")

    def test_get_task_value(self):
        task_value = stackdriver.get_task_value()
        self.assertNotEqual(task_value, "")

    def test_namespaced_views(self):
        view_name = "view-1"
        expected_view_name_namespaced = (
            "custom.googleapis.com/opencensus/{}".format(view_name))
        view_name_namespaced = stackdriver.namespaced_view_name(view_name, "")
        self.assertEqual(expected_view_name_namespaced, view_name_namespaced)

        expected_view_name_namespaced = "kubernetes.io/myorg/%s" % view_name
        view_name_namespaced = stackdriver.namespaced_view_name(
            view_name, "kubernetes.io/myorg")
        self.assertEqual(expected_view_name_namespaced, view_name_namespaced)

    def test_stackdriver_register_exporter(self):
        stats = stats_module.stats
        view_manager = stats.view_manager

        exporter = mock.Mock()
        if len(view_manager.measure_to_view_map.exporters) > 0:
            view_manager.unregister_exporter(
                view_manager.measure_to_view_map.exporters[0])
        view_manager.register_exporter(exporter)

        registered_exporters = len(view_manager.measure_to_view_map.exporters)

        self.assertEqual(registered_exporters, 1)

    @mock.patch('os.getpid', return_value=12345)
    @mock.patch(
        'platform.uname',
        return_value=('system', 'node', 'release', 'version', 'machine',
                      'processor'))
    def test_get_task_value_with_hostname(self, mock_uname, mock_pid):
        self.assertEqual(stackdriver.get_task_value(), "py-12345@node")

    @mock.patch('os.getpid', return_value=12345)
    @mock.patch(
        'platform.uname',
        return_value=('system', '', 'release', 'version', 'machine',
                      'processor'))
    def test_get_task_value_without_hostname(self, mock_uname, mock_pid):
        self.assertEqual(stackdriver.get_task_value(), "py-12345@localhost")

    def test_get_metric_descriptor(self):
        exporter = stackdriver.StackdriverStatsExporter(
            options=stackdriver.Options(
                default_monitoring_labels={'dk': 'dd'},
                project_id='project_id'),
            client=mock.Mock())

        oc_md = metric_descriptor.MetricDescriptor(
            name='name',
            description='description',
            unit='unit',
            type_=metric_descriptor.MetricDescriptorType.GAUGE_INT64,
            label_keys=[label_key.LabelKey('ck', 'cd')]
        )

        sd_md = exporter.get_metric_descriptor(oc_md)
        self.assertEqual(
            sd_md.metric_kind,
            monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE)
        self.assertEqual(
            sd_md.value_type,
            monitoring_v3.enums.MetricDescriptor.ValueType.INT64)

        self.assertIsInstance(sd_md, monitoring_v3.types.MetricDescriptor)
        exporter.client.create_metric_descriptor.assert_not_called()

    def test_get_metric_descriptor_bad_type(self):
        exporter = stackdriver.StackdriverStatsExporter(
            options=stackdriver.Options(project_id='project_id'),
            client=mock.Mock())

        bad_type_oc_md = metric_descriptor.MetricDescriptor(
            name='name',
            description='description',
            unit='unit',
            # Need a valid type to create the descriptor
            type_=metric_descriptor.MetricDescriptorType.GAUGE_INT64,
            label_keys=[label_key.LabelKey('key', 'description')]
        )
        bad_type_oc_md._type = 100

        with self.assertRaises(TypeError):
            exporter.get_metric_descriptor(bad_type_oc_md)

    def test_get_metric_descriptor_custom_prefix(self):

        exporter = stackdriver.StackdriverStatsExporter(
            options=stackdriver.Options(
                default_monitoring_labels={'dk': 'dd'},
                metric_prefix='metric_prefix',
                project_id='project_id'),
            client=mock.Mock())

        oc_md = metric_descriptor.MetricDescriptor(
            name='name',
            description='description',
            unit='unit',
            type_=metric_descriptor.MetricDescriptorType.GAUGE_INT64,
            label_keys=[label_key.LabelKey('ck', 'cd')]
        )

        sd_md = exporter.get_metric_descriptor(oc_md)
        self.assertIn('metric_prefix', sd_md.type)
        self.assertIn('metric_prefix', sd_md.name)

    def test_register_metric_descriptor(self):
        exporter = stackdriver.StackdriverStatsExporter(
            options=stackdriver.Options(
                metric_prefix='metric_prefix',
                project_id='project_id'),
            client=mock.Mock())

        oc_md = metric_descriptor.MetricDescriptor(
            name='name',
            description='description',
            unit='unit',
            type_=metric_descriptor.MetricDescriptorType.GAUGE_INT64,
            label_keys=[label_key.LabelKey('key', 'description')]
        )

        exporter.register_metric_descriptor(oc_md)
        self.assertEqual(
            exporter.client.create_metric_descriptor.call_count,
            1
        )
        exporter.register_metric_descriptor(oc_md)
        self.assertEqual(
            exporter.client.create_metric_descriptor.call_count,
            1
        )

    def test_export_metrics(self):
        lv = label_value.LabelValue('val')
        val = value.ValueLong(value=123)
        dt = datetime(2019, 3, 20, 21, 34, 0, 537954)
        pp = point.Point(value=val, timestamp=dt)

        ts = [
            time_series.TimeSeries(label_values=[lv], points=[pp],
                                   start_timestamp=utils.to_iso_str(dt))
        ]

        desc = metric_descriptor.MetricDescriptor(
            name='name',
            description='description',
            unit='unit',
            type_=metric_descriptor.MetricDescriptorType.GAUGE_INT64,
            label_keys=[label_key.LabelKey('key', 'description')]
        )

        mm = metric.Metric(descriptor=desc, time_series=ts)

        exporter = stackdriver.StackdriverStatsExporter(client=mock.Mock())
        exporter.export_metrics([mm])

        self.assertEqual(exporter.client.create_time_series.call_count, 1)
        sd_args = exporter.client.create_time_series.call_args[0][1]
        self.assertEqual(len(sd_args), 1)
        [sd_arg] = exporter.client.create_time_series.call_args[0][1]
        self.assertEqual(sd_arg.points[0].value.int64_value, 123)


class MockPeriodicTask(object):
    """Testing mock of metrics.transport.PeriodicTask.

    Simulate calling export asynchronously from another thread synchronously
    from this one.
    """
    def __init__(self, func, interval=None, **kwargs):
        self.func = func
        self.logger = mock.Mock()
        self.start = mock.Mock()
        self.run = mock.Mock()

    def step(self):
        try:
            self.func()
        except transport_module.TransportError as ex:
            self.logger.exception(ex)
            self.stop()
        except Exception:
            self.logger.exception("Error handling metric export")


@mock.patch('opencensus.ext.stackdriver.stats_exporter'
            '.monitoring_v3.MetricServiceClient')
class TestAsyncStatsExport(unittest.TestCase):
    """Check that metrics are exported using the exporter thread."""

    def setUp(self):
        patcher = mock.patch(
            'opencensus.metrics.transport.PeriodicTask',
            MockPeriodicTask)
        patcher.start()
        self.addCleanup(patcher.stop)

    @mock.patch('opencensus.ext.stackdriver.stats_exporter'
                '.stats.stats')
    def test_export_empty(self, mock_stats, mock_client):
        """Check that we don't attempt to export empty metric sets."""

        mock_stats.get_metrics.return_value = []

        exporter, transport = stackdriver.new_stats_exporter(
            stackdriver.Options(project_id=1))

        transport.step()
        exporter.client.create_metric_descriptor.assert_not_called()
        exporter.client.create_time_series.assert_not_called()

    @mock.patch('opencensus.ext.stackdriver.stats_exporter'
                '.stats.stats')
    def test_export_single_metric(self, mock_stats, mock_client):
        """Check that we can export a set of a single metric."""

        lv = label_value.LabelValue('val')
        val = value.ValueLong(value=123)
        dt = datetime(2019, 3, 20, 21, 34, 0, 537954)
        pp = point.Point(value=val, timestamp=dt)

        ts = [
            time_series.TimeSeries(label_values=[lv], points=[pp],
                                   start_timestamp=utils.to_iso_str(dt))
        ]

        desc = metric_descriptor.MetricDescriptor(
            name='name2',
            description='description2',
            unit='unit2',
            type_=metric_descriptor.MetricDescriptorType.GAUGE_INT64,
            label_keys=[label_key.LabelKey('key', 'description')]
        )

        mm = metric.Metric(descriptor=desc, time_series=ts)
        mock_stats.get_metrics.return_value = [mm]

        exporter, transport = stackdriver.new_stats_exporter(
            stackdriver.Options(project_id=1))

        transport.step()

        exporter.client.create_metric_descriptor.assert_called()
        self.assertEqual(
            exporter.client.create_metric_descriptor.call_count,
            1)
        md_call_arg =\
            exporter.client.create_metric_descriptor.call_args[0][1]
        self.assertEqual(
            md_call_arg.metric_kind,
            monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE
        )
        self.assertEqual(
            md_call_arg.value_type,
            monitoring_v3.enums.MetricDescriptor.ValueType.INT64
        )

        exporter.client.create_time_series.assert_called()
        self.assertEqual(
            exporter.client.create_time_series.call_count,
            1)
        ts_call_arg = exporter.client.create_time_series.call_args[0][1]
        self.assertEqual(len(ts_call_arg), 1)
        self.assertEqual(len(ts_call_arg[0].points), 1)
        self.assertEqual(ts_call_arg[0].points[0].value.int64_value, 123)


class TestCreateTimeseries(unittest.TestCase):

    def setUp(self):
        patcher = mock.patch(
            'opencensus.ext.stackdriver.stats_exporter.stats.stats',
            stats_module._Stats())
        patcher.start()
        self.addCleanup(patcher.stop)

    def check_labels(self,
                     actual_labels,
                     expected_labels,
                     include_opencensus=False):
        actual_labels = dict(actual_labels)
        if include_opencensus:
            opencensus_tag = actual_labels.pop(stackdriver.OPENCENSUS_TASK)
            self.assertIsNotNone(opencensus_tag)
            self.assertIn("py-", opencensus_tag)
        self.assertDictEqual(actual_labels, expected_labels)

    @mock.patch('opencensus.ext.stackdriver.stats_exporter.'
                'monitored_resource.get_instance',
                return_value=None)
    def test_create_batched_time_series(self, monitor_resource_mock):
        client = mock.Mock()
        v_data = view_data_module.ViewData(
            view=VIDEO_SIZE_VIEW,
            start_time=TEST_TIME_STR,
            end_time=TEST_TIME_STR)
        v_data.record(context=tag_map_module.TagMap(), value=2, timestamp=None)
        view_data = [v_data]

        option = stackdriver.Options(project_id="project-test")
        exporter = stackdriver.StackdriverStatsExporter(
            options=option, client=client)

        view_data = [metric_utils.view_data_to_metric(view_data[0], TEST_TIME)]

        time_series_batches = exporter.create_batched_time_series(view_data, 1)

        self.assertEqual(len(time_series_batches), 1)
        [time_series_batch] = time_series_batches
        self.assertEqual(len(time_series_batch), 1)
        [time_series] = time_series_batch
        self.assertEqual(
            time_series.metric.type,
            'custom.googleapis.com/opencensus/' + VIDEO_SIZE_VIEW_NAME)
        self.check_labels(
            time_series.metric.labels, {}, include_opencensus=True)

    @mock.patch('opencensus.ext.stackdriver.stats_exporter.'
                'monitored_resource.get_instance',
                return_value=None)
    def test_create_batched_time_series_with_many(self, monitor_resource_mock):
        client = mock.Mock()

        # First view with 3
        view_name1 = "view-name1"
        view1 = view_module.View(view_name1, "test description", ['test'],
                                 VIDEO_SIZE_MEASURE,
                                 aggregation_module.LastValueAggregation())
        v_data1 = view_data_module.ViewData(
            view=view1, start_time=TEST_TIME_STR, end_time=TEST_TIME_STR)
        v_data1.record(context=tag_map_module.TagMap({'test': '1'}), value=7,
                       timestamp=None)
        v_data1.record(context=tag_map_module.TagMap({'test': '2'}), value=5,
                       timestamp=None)
        v_data1.record(context=tag_map_module.TagMap({'test': '3'}), value=3,
                       timestamp=None)

        # Second view with 2
        view_name2 = "view-name2"
        view2 = view_module.View(view_name2, "test description", ['test'],
                                 VIDEO_SIZE_MEASURE,
                                 aggregation_module.LastValueAggregation())
        v_data2 = view_data_module.ViewData(
            view=view2, start_time=TEST_TIME_STR, end_time=TEST_TIME_STR)
        v_data2.record(context=tag_map_module.TagMap({'test': '1'}), value=7,
                       timestamp=None)
        v_data2.record(context=tag_map_module.TagMap({'test': '2'}), value=5,
                       timestamp=None)

        view_data = [v_data1, v_data2]
        view_data = [metric_utils.view_data_to_metric(vd, TEST_TIME)
                     for vd in view_data]

        option = stackdriver.Options(project_id="project-test")
        exporter = stackdriver.StackdriverStatsExporter(
            options=option, client=client)

        time_series_batches = exporter.create_batched_time_series(view_data, 2)

        self.assertEqual(len(time_series_batches), 3)
        [tsb1, tsb2, tsb3] = time_series_batches
        self.assertEqual(len(tsb1), 2)
        self.assertEqual(len(tsb2), 2)
        self.assertEqual(len(tsb3), 1)

    def setup_create_timeseries_test(self):
        client = mock.Mock()
        execution_context.clear()

        option = stackdriver.Options(
            project_id="project-test", resource="global")
        exporter = stackdriver.StackdriverStatsExporter(
            options=option, client=client)

        stats = stats_module.stats
        view_manager = stats.view_manager
        stats_recorder = stats.stats_recorder

        if len(view_manager.measure_to_view_map.exporters) > 0:
            view_manager.unregister_exporter(
                view_manager.measure_to_view_map.exporters[0])

        view_manager.register_exporter(exporter)
        return view_manager, stats_recorder, exporter

    @mock.patch('opencensus.ext.stackdriver.stats_exporter.'
                'monitored_resource.get_instance',
                return_value=None)
    def test_create_timeseries(self, monitor_resource_mock):
        view_manager, stats_recorder, exporter = \
            self.setup_create_timeseries_test()

        view_manager.register_view(VIDEO_SIZE_VIEW)

        tag_value = tag_value_module.TagValue("1200")
        tag_map = tag_map_module.TagMap()
        tag_map.insert(FRONTEND_KEY, tag_value)

        measure_map = stats_recorder.new_measurement_map()
        measure_map.measure_int_put(VIDEO_SIZE_MEASURE, 25 * MiB)
        measure_map.record(tag_map)

        v_data = measure_map.measure_to_view_map.get_view(
            VIDEO_SIZE_VIEW_NAME, None)

        v_data = metric_utils.view_data_to_metric(v_data, TEST_TIME)

        time_series_list = exporter.create_time_series_list(v_data)

        self.assertEqual(len(time_series_list), 1)
        time_series = time_series_list[0]
        self.assertEqual(time_series.resource.type, "global")
        self.assertEqual(
            time_series_list[0].metric.type,
            "custom.googleapis.com/opencensus/my.org/views/video_size_test2")
        self.check_labels(
            time_series.metric.labels, {FRONTEND_KEY_CLEAN: "1200"},
            include_opencensus=True)
        self.assertIsNotNone(time_series.resource)

        self.assertEqual(len(time_series.points), 1)
        value = time_series.points[0].value
        self.assertEqual(value.distribution_value.count, 1)

        time_series_list = exporter.create_time_series_list(v_data)

        self.assertEqual(len(time_series_list), 1)
        time_series = time_series_list[0]
        self.check_labels(
            time_series.metric.labels, {FRONTEND_KEY_CLEAN: "1200"},
            include_opencensus=True)
        self.assertIsNotNone(time_series.resource)

        self.assertEqual(len(time_series.points), 1)
        value = time_series.points[0].value
        self.assertEqual(value.distribution_value.count, 1)

    @mock.patch('opencensus.ext.stackdriver.stats_exporter.'
                'monitored_resource.get_instance')
    def test_create_timeseries_with_resource(self, monitor_resource_mock):

        client = mock.Mock()
        execution_context.clear()

        option = stackdriver.Options(project_id="project-test", resource="")
        exporter = stackdriver.StackdriverStatsExporter(
            options=option, client=client)

        stats = stats_module.stats
        view_manager = stats.view_manager
        stats_recorder = stats.stats_recorder

        if len(view_manager.measure_to_view_map.exporters) > 0:
            view_manager.unregister_exporter(
                view_manager.measure_to_view_map.exporters[0])

        view_manager.register_exporter(exporter)
        view_manager.register_view(VIDEO_SIZE_VIEW)

        tag_value = tag_value_module.TagValue("1200")
        tag_map = tag_map_module.TagMap()
        tag_map.insert(FRONTEND_KEY, tag_value)

        measure_map = stats_recorder.new_measurement_map()
        measure_map.measure_int_put(VIDEO_SIZE_MEASURE, 25 * MiB)
        measure_map.record(tag_map)

        v_data = measure_map.measure_to_view_map.get_view(
            VIDEO_SIZE_VIEW_NAME, None)

        v_data = metric_utils.view_data_to_metric(v_data, TEST_TIME)

        # check for gce_instance monitored resource
        mocked_labels = {
            'instance_id': 'my-instance',
            'project_id': 'my-project',
            'zone': 'us-east1',
            'pod_id': 'localhost',
            'namespace_id': 'namespace'
        }

        mock_resource = mock.Mock()
        mock_resource.get_type.return_value = 'gce_instance'
        mock_resource.get_labels.return_value = mocked_labels
        monitor_resource_mock.return_value = mock_resource

        time_series_list = exporter.create_time_series_list(v_data)
        self.assertEqual(len(time_series_list), 1)
        time_series = time_series_list[0]
        self.assertEqual(time_series.resource.type, "gce_instance")
        self.check_labels(
            time_series.resource.labels, {
                'instance_id': 'my-instance',
                'project_id': 'my-project',
                'zone': 'us-east1',
            })
        self.assertEqual(
            time_series.metric.type,
            "custom.googleapis.com/opencensus/my.org/views/video_size_test2")
        self.assertIsNotNone(time_series)

        time_series_list = exporter.create_time_series_list(v_data)
        self.assertEqual(len(time_series_list), 1)
        time_series = time_series_list[0]

        self.assertEqual(
            time_series.metric.type,
            "custom.googleapis.com/opencensus/my.org/views/video_size_test2")

        # check for gke_container monitored resource
        mocked_labels = {
            'instance_id': 'my-instance',
            'project_id': 'my-project',
            'zone': 'us-east1',
            'pod_id': 'localhost',
            'cluster_name': 'cluster',
            'namespace_id': 'namespace'
        }

        mock_resource = mock.Mock()
        mock_resource.get_type.return_value = 'gke_container'
        mock_resource.get_labels.return_value = mocked_labels
        monitor_resource_mock.return_value = mock_resource

        time_series_list = exporter.create_time_series_list(v_data)
        self.assertEqual(len(time_series_list), 1)
        time_series = time_series_list[0]
        self.assertEqual(time_series.resource.type, "k8s_container")
        self.check_labels(
            time_series.resource.labels, {
                'project_id': 'my-project',
                'location': 'us-east1',
                'cluster_name': 'cluster',
                'pod_name': 'localhost',
                'namespace_name': 'namespace',
            })
        self.assertEqual(
            time_series.metric.type,
            "custom.googleapis.com/opencensus/my.org/views/video_size_test2")
        self.assertIsNotNone(time_series)

        # check for aws_ec2_instance monitored resource
        mocked_labels = {
            'instance_id': 'my-instance',
            'aws_account': 'my-project',
            'region': 'us-east1',
        }

        mock_resource = mock.Mock()
        mock_resource.get_type.return_value = 'aws_ec2_instance'
        mock_resource.get_labels.return_value = mocked_labels
        monitor_resource_mock.return_value = mock_resource

        time_series_list = exporter.create_time_series_list(v_data)
        self.assertEqual(len(time_series_list), 1)
        time_series = time_series_list[0]
        self.assertEqual(time_series.resource.type, "aws_ec2_instance")
        self.check_labels(
            time_series.resource.labels, {
                'instance_id': 'my-instance',
                'aws_account': 'my-project',
                'region': 'aws:us-east1',
            })
        self.assertEqual(
            time_series.metric.type,
            "custom.googleapis.com/opencensus/my.org/views/video_size_test2")
        self.assertIsNotNone(time_series)

        # check for out of box monitored resource
        mock_resource = mock.Mock()
        mock_resource.get_type.return_value = ''
        mock_resource.get_labels.return_value = mock.Mock()
        monitor_resource_mock.return_value = mock_resource

        time_series_list = exporter.create_time_series_list(v_data)
        self.assertEqual(len(time_series_list), 1)
        time_series = time_series_list[0]
        self.assertEqual(time_series.resource.type, 'global')
        self.check_labels(time_series.resource.labels, {})
        self.assertEqual(
            time_series.metric.type,
            "custom.googleapis.com/opencensus/my.org/views/video_size_test2")
        self.assertIsNotNone(time_series)

    @mock.patch('opencensus.ext.stackdriver.stats_exporter.'
                'monitored_resource.get_instance',
                return_value=None)
    def test_create_timeseries_str_tagvalue(self, monitor_resource_mock):
        view_manager, stats_recorder, exporter = \
            self.setup_create_timeseries_test()

        agg_1 = aggregation_module.LastValueAggregation(value=2)
        view_name1 = "view-name1"
        new_view1 = view_module.View(
            view_name1, "processed video size over time", [FRONTEND_KEY_INT],
            VIDEO_SIZE_MEASURE_2, agg_1)

        view_manager.register_view(new_view1)

        tag_value_int = tag_value_module.TagValue("Abc")
        tag_map = tag_map_module.TagMap()
        tag_map.insert(FRONTEND_KEY_INT, tag_value_int)

        measure_map = stats_recorder.new_measurement_map()
        measure_map.measure_int_put(VIDEO_SIZE_MEASURE_2, 25 * MiB)
        measure_map.record(tag_map)

        v_data = measure_map.measure_to_view_map.get_view(view_name1, None)

        v_data = metric_utils.view_data_to_metric(v_data, TEST_TIME)

        time_series_list = exporter.create_time_series_list(v_data)
        self.assertEqual(len(time_series_list), 1)
        time_series = time_series_list[0]

        self.check_labels(
            time_series.metric.labels, {FRONTEND_KEY_INT_CLEAN: "Abc"},
            include_opencensus=True)
        self.assertIsNotNone(time_series.resource)

        self.assertEqual(len(time_series.points), 1)
        expected_value = monitoring_v3.types.TypedValue()
        # TODO: #565
        expected_value.double_value = 25.0 * MiB
        self.assertEqual(time_series.points[0].value, expected_value)

    @mock.patch('opencensus.ext.stackdriver.stats_exporter.'
                'monitored_resource.get_instance',
                return_value=None)
    def test_create_timeseries_str_tagvalue_count_aggregtation(
            self, monitor_resource_mock):
        view_manager, stats_recorder, exporter = \
            self.setup_create_timeseries_test()

        agg_1 = aggregation_module.CountAggregation(count=2)
        view_name1 = "view-name1"
        new_view1 = view_module.View(
            view_name1, "processed video size over time", [FRONTEND_KEY_INT],
            VIDEO_SIZE_MEASURE_2, agg_1)

        view_manager.register_view(new_view1)

        tag_value_int = tag_value_module.TagValue("Abc")
        tag_map = tag_map_module.TagMap()
        tag_map.insert(FRONTEND_KEY_INT, tag_value_int)

        measure_map = stats_recorder.new_measurement_map()
        measure_map.measure_int_put(VIDEO_SIZE_MEASURE_2, 25 * MiB)
        measure_map.record(tag_map)

        v_data = measure_map.measure_to_view_map.get_view(view_name1, None)

        v_data = metric_utils.view_data_to_metric(v_data, TEST_TIME)

        time_series_list = exporter.create_time_series_list(v_data)
        self.assertEqual(len(time_series_list), 1)
        time_series = time_series_list[0]
        self.check_labels(
            time_series.metric.labels, {FRONTEND_KEY_INT_CLEAN: "Abc"},
            include_opencensus=True)
        self.assertIsNotNone(time_series.resource)

        self.assertEqual(len(time_series.points), 1)
        expected_value = monitoring_v3.types.TypedValue()
        expected_value.int64_value = 3
        self.assertEqual(time_series.points[0].value, expected_value)

    @mock.patch('opencensus.ext.stackdriver.stats_exporter.'
                'monitored_resource.get_instance',
                return_value=None)
    def test_create_timeseries_last_value_float_tagvalue(
            self, monitor_resource_mock):
        view_manager, stats_recorder, exporter = \
            self.setup_create_timeseries_test()

        agg_2 = aggregation_module.LastValueAggregation(value=2.2 * MiB)
        view_name2 = "view-name2"
        new_view2 = view_module.View(
            view_name2, "processed video size over time", [FRONTEND_KEY_FLOAT],
            VIDEO_SIZE_MEASURE_FLOAT, agg_2)

        view_manager.register_view(new_view2)

        tag_value_float = tag_value_module.TagValue("Abc")
        tag_map = tag_map_module.TagMap()
        tag_map.insert(FRONTEND_KEY_FLOAT, tag_value_float)

        measure_map = stats_recorder.new_measurement_map()
        measure_map.measure_float_put(VIDEO_SIZE_MEASURE_FLOAT, 25.7 * MiB)
        measure_map.record(tag_map)

        v_data = measure_map.measure_to_view_map.get_view(view_name2, None)

        v_data = metric_utils.view_data_to_metric(v_data, TEST_TIME)

        time_series_list = exporter.create_time_series_list(v_data)
        self.assertEqual(len(time_series_list), 1)
        time_series = time_series_list[0]
        self.check_labels(
            time_series.metric.labels, {FRONTEND_KEY_FLOAT_CLEAN: "Abc"},
            include_opencensus=True)
        self.assertIsNotNone(time_series.resource)

        self.assertEqual(len(time_series.points), 1)
        expected_value = monitoring_v3.types.TypedValue()
        expected_value.double_value = 25.7 * MiB
        self.assertEqual(time_series.points[0].value, expected_value)

    @mock.patch('opencensus.ext.stackdriver.stats_exporter.'
                'monitored_resource.get_instance',
                return_value=None)
    def test_create_timeseries_float_tagvalue(self, monitor_resource_mock):
        client = mock.Mock()

        option = stackdriver.Options(
            project_id="project-test", resource="global")
        exporter = stackdriver.StackdriverStatsExporter(
            options=option, client=client)

        stats = stats_module.stats
        view_manager = stats.view_manager
        stats_recorder = stats.stats_recorder

        if len(view_manager.measure_to_view_map.exporters) > 0:
            view_manager.unregister_exporter(
                view_manager.measure_to_view_map.exporters[0])

        view_manager.register_exporter(exporter)

        agg_3 = aggregation_module.SumAggregation(sum=2.2)
        view_name3 = "view-name3"
        new_view3 = view_module.View(
            view_name3, "processed video size over time", [FRONTEND_KEY_FLOAT],
            VIDEO_SIZE_MEASURE_FLOAT, agg_3)

        view_manager.register_view(new_view3)

        tag_value_float = tag_value_module.TagValue("1200")
        tag_map = tag_map_module.TagMap()
        tag_map.insert(FRONTEND_KEY_FLOAT, tag_value_float)

        measure_map = stats_recorder.new_measurement_map()
        measure_map.measure_float_put(VIDEO_SIZE_MEASURE_FLOAT, 25 * MiB)
        measure_map.record(tag_map)

        v_data = measure_map.measure_to_view_map.get_view(view_name3, None)

        v_data = metric_utils.view_data_to_metric(v_data, TEST_TIME)

        time_series_list = exporter.create_time_series_list(v_data)
        self.assertEqual(len(time_series_list), 1)
        [time_series] = time_series_list
        self.assertEqual(time_series.metric.type,
                         "custom.googleapis.com/opencensus/view-name3")
        self.check_labels(
            time_series.metric.labels, {FRONTEND_KEY_FLOAT_CLEAN: "1200"},
            include_opencensus=True)
        self.assertIsNotNone(time_series.resource)

        self.assertEqual(len(time_series.points), 1)
        expected_value = monitoring_v3.types.TypedValue()
        expected_value.double_value = 2.2 + 25 * MiB
        self.assertEqual(time_series.points[0].value, expected_value)

    @mock.patch('opencensus.ext.stackdriver.stats_exporter.'
                'monitored_resource.get_instance',
                return_value=None)
    def test_create_timeseries_multiple_tag_values(self,
                                                   monitoring_resoure_mock):
        view_manager, stats_recorder, exporter = \
            self.setup_create_timeseries_test()

        view_manager.register_view(VIDEO_SIZE_VIEW)

        measure_map = stats_recorder.new_measurement_map()

        # Add first point with one tag value
        tag_map = tag_map_module.TagMap()
        tag_map.insert(FRONTEND_KEY, tag_value_module.TagValue("1200"))
        measure_map.measure_int_put(VIDEO_SIZE_MEASURE, 25 * MiB)
        measure_map.record(tag_map)

        # Add second point with different tag value
        tag_map = tag_map_module.TagMap()
        tag_map.insert(FRONTEND_KEY, tag_value_module.TagValue("1400"))
        measure_map.measure_int_put(VIDEO_SIZE_MEASURE, 12 * MiB)
        measure_map.record(tag_map)

        v_data = measure_map.measure_to_view_map.get_view(
            VIDEO_SIZE_VIEW_NAME, None)

        v_data = metric_utils.view_data_to_metric(v_data, TEST_TIME)

        time_series_list = exporter.create_time_series_list(v_data)

        self.assertEqual(len(time_series_list), 2)
        ts_by_frontend = {
            ts.metric.labels.get(FRONTEND_KEY_CLEAN): ts
            for ts in time_series_list
        }
        self.assertEqual(set(ts_by_frontend.keys()), {"1200", "1400"})
        ts1 = ts_by_frontend["1200"]
        ts2 = ts_by_frontend["1400"]

        # Verify first time series
        self.assertEqual(ts1.resource.type, "global")
        self.assertEqual(
            ts1.metric.type,
            "custom.googleapis.com/opencensus/my.org/views/video_size_test2")
        self.assertIsNotNone(ts1.resource)

        self.assertEqual(len(ts1.points), 1)
        value1 = ts1.points[0].value
        self.assertEqual(value1.distribution_value.count, 1)

        # Verify second time series
        self.assertEqual(ts2.resource.type, "global")
        self.assertEqual(
            ts2.metric.type,
            "custom.googleapis.com/opencensus/my.org/views/video_size_test2")
        self.assertIsNotNone(ts2.resource)

        self.assertEqual(len(ts2.points), 1)
        value2 = ts2.points[0].value
        self.assertEqual(value2.distribution_value.count, 1)

    @mock.patch('opencensus.ext.stackdriver.stats_exporter.'
                'monitored_resource.get_instance',
                return_value=None)
    def test_create_timeseries_disjoint_tags(self, monitoring_resoure_mock):
        view_manager, stats_recorder, exporter = \
            self.setup_create_timeseries_test()

        # Register view with two tags
        view_name = "view-name"
        view = view_module.View(view_name, "test description",
                                [FRONTEND_KEY, FRONTEND_KEY_FLOAT],
                                VIDEO_SIZE_MEASURE,
                                aggregation_module.SumAggregation())

        view_manager.register_view(view)

        # Add point with one tag in common and one different tag
        measure_map = stats_recorder.new_measurement_map()
        tag_map = tag_map_module.TagMap()
        tag_map.insert(FRONTEND_KEY, tag_value_module.TagValue("1200"))
        tag_map.insert(FRONTEND_KEY_STR, tag_value_module.TagValue("1800"))
        measure_map.measure_int_put(VIDEO_SIZE_MEASURE, 25 * MiB)
        measure_map.record(tag_map)

        v_data = measure_map.measure_to_view_map.get_view(view_name, None)

        v_data = metric_utils.view_data_to_metric(v_data, TEST_TIME)

        time_series_list = exporter.create_time_series_list(v_data)

        self.assertEqual(len(time_series_list), 1)
        [time_series] = time_series_list

        # Verify first time series
        self.assertEqual(time_series.resource.type, "global")
        self.assertEqual(time_series.metric.type,
                         "custom.googleapis.com/opencensus/" + view_name)
        self.check_labels(
            time_series.metric.labels, {FRONTEND_KEY_CLEAN: "1200"},
            include_opencensus=True)
        self.assertIsNotNone(time_series.resource)

        self.assertEqual(len(time_series.points), 1)
        expected_value = monitoring_v3.types.TypedValue()
        # TODO: #565
        expected_value.double_value = 25.0 * MiB
        self.assertEqual(time_series.points[0].value, expected_value)

    def test_create_timeseries_from_distribution(self):
        """Check for explicit 0-bound bucket for SD export."""
        agg = aggregation_module.DistributionAggregation(
            aggregation_type=aggregation_module.Type.DISTRIBUTION)

        view = view_module.View(
            name="example.org/test_view",
            description="example.org/test_view",
            columns=['tag_key'],
            measure=mock.Mock(),
            aggregation=agg,
        )

        v_data = view_data_module.ViewData(
            view=view,
            start_time=TEST_TIME_STR,
            end_time=TEST_TIME_STR,
        )

        # Aggregation over (10 * range(10)) for buckets [2, 4, 6, 8]
        dad = aggregation_data_module.DistributionAggregationData(
            mean_data=4.5,
            count_data=100,
            sum_of_sqd_deviations=825,
            counts_per_bucket=[20, 20, 20, 20, 20],
            bounds=[2, 4, 6, 8],
            exemplars={mock.Mock() for ii in range(5)}
        )
        v_data._tag_value_aggregation_data_map = {('tag_value',): dad}

        v_data = metric_utils.view_data_to_metric(v_data, TEST_TIME)

        exporter = stackdriver.StackdriverStatsExporter()
        time_series_list = exporter.create_time_series_list(v_data)
        self.assertEqual(len(time_series_list), 1)
        [time_series] = time_series_list

        self.check_labels(
            time_series.metric.labels, {'tag_key': 'tag_value'},
            include_opencensus=True)
        self.assertEqual(len(time_series.points), 1)
        [point] = time_series.points
        dv = point.value.distribution_value
        self.assertEqual(100, dv.count)
        self.assertEqual(825.0, dv.sum_of_squared_deviation)
        self.assertEqual([0, 20, 20, 20, 20, 20], dv.bucket_counts)
        self.assertEqual([0, 2, 4, 6, 8],
                         dv.bucket_options.explicit_buckets.bounds)

    def test_create_timeseries_multiple_tags(self):
        """Check that exporter creates timeseries for multiple tag values.

        create_time_series_list should return a time series for each set of
        values in the tag value aggregation map.
        """
        agg = aggregation_module.CountAggregation(
            aggregation_type=aggregation_module.Type.COUNT)

        view = view_module.View(
            name="example.org/test_view",
            description="example.org/test_view",
            columns=[tag_key_module.TagKey('color'),
                     tag_key_module.TagKey('shape')],
            measure=mock.Mock(),
            aggregation=agg,
        )

        v_data = view_data_module.ViewData(
            view=view,
            start_time=TEST_TIME_STR,
            end_time=TEST_TIME_STR,
        )

        rs_count = aggregation_data_module.CountAggregationData(10)
        bc_count = aggregation_data_module.CountAggregationData(20)
        v_data._tag_value_aggregation_data_map = {
            ('red', 'square'): rs_count,
            ('blue', 'circle'): bc_count,
        }

        v_data = metric_utils.view_data_to_metric(v_data, TEST_TIME)

        exporter = stackdriver.StackdriverStatsExporter()
        time_series_list = exporter.create_time_series_list(v_data)

        self.assertEqual(len(time_series_list), 2)
        self.assertEqual(len(time_series_list[0].points), 1)
        self.assertEqual(len(time_series_list[1].points), 1)

        ts_by_color = {ts.metric.labels.get('color'): ts
                       for ts in time_series_list}
        rs_ts = ts_by_color['red']
        bc_ts = ts_by_color['blue']
        self.assertEqual(rs_ts.metric.labels.get('shape'), 'square')
        self.assertEqual(bc_ts.metric.labels.get('shape'), 'circle')
        self.assertEqual(rs_ts.points[0].value.int64_value, 10)
        self.assertEqual(bc_ts.points[0].value.int64_value, 20)

    def test_create_timeseries_invalid_aggregation(self):
        v_data = mock.Mock(spec=view_data_module.ViewData)
        v_data.view.name = "example.org/base_view"
        v_data.view.columns = [tag_key_module.TagKey('base_key')]
        v_data.view.aggregation.aggregation_type = \
            aggregation_module.Type.NONE
        v_data.start_time = TEST_TIME_STR
        v_data.end_time = TEST_TIME_STR

        base_data = aggregation_data_module.BaseAggregationData(10)
        v_data.tag_value_aggregation_data_map = {
            (None,): base_data,
        }

        exporter = stackdriver.StackdriverStatsExporter(
            options=mock.Mock(),
            client=mock.Mock(),
        )
        self.assertRaises(TypeError, exporter.create_time_series_list, v_data,
                          "", "")
