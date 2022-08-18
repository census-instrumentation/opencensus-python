# Copyright 2019, OpenCensus Authors
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
import os
import shutil
import unittest
from datetime import datetime

import mock

from opencensus.common import utils
from opencensus.ext.azure.common.protocol import DataPoint
from opencensus.ext.azure.common.transport import TransportStatusCode
from opencensus.ext.azure.metrics_exporter import (
    MetricsExporter,
    new_metrics_exporter,
    standard_metrics,
)
from opencensus.ext.azure.statsbeat.statsbeat_metrics import (
    _ATTACH_METRIC_NAME,
    _REQ_SUCCESS_NAME,
)
from opencensus.metrics import label_key, label_value
from opencensus.metrics.export import (
    metric,
    metric_descriptor,
    point,
    time_series,
    value,
)
from opencensus.metrics.export.metric_descriptor import MetricDescriptorType

TEST_FOLDER = os.path.abspath('.test.metrics.exporter')


def setUpModule():
    os.makedirs(TEST_FOLDER)


def tearDownModule():
    shutil.rmtree(TEST_FOLDER)


def create_metric():
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
    return mm


def create_metric_ts():
    lv = label_value.LabelValue('val')
    lv2 = label_value.LabelValue('val2')
    val = value.ValueLong(value=123)
    dt = datetime(2019, 3, 20, 21, 34, 0, 537954)
    pp = point.Point(value=val, timestamp=dt)

    ts = [
        time_series.TimeSeries(
            label_values=[lv],
            points=[pp],
            start_timestamp=utils.to_iso_str(dt)
        ),
        time_series.TimeSeries(
            label_values=[lv2],
            points=[pp],
            start_timestamp=utils.to_iso_str(dt)
        ),
    ]

    desc = metric_descriptor.MetricDescriptor(
        name='name',
        description='description',
        unit='unit',
        type_=metric_descriptor.MetricDescriptorType.GAUGE_INT64,
        label_keys=[label_key.LabelKey('key', 'description')]
    )

    mm = metric.Metric(descriptor=desc, time_series=ts)
    return mm


def create_stats_metric(name, num):
    lv = label_value.LabelValue('val')
    val = value.ValueLong(value=num)
    dt = datetime(2019, 3, 20, 21, 34, 0, 537954)
    pp = point.Point(value=val, timestamp=dt)

    ts = [
        time_series.TimeSeries(
            label_values=[lv],
            points=[pp],
            start_timestamp=utils.to_iso_str(dt)
        )
    ]

    desc = metric_descriptor.MetricDescriptor(
        name=name,
        description='description',
        unit='unit',
        type_=metric_descriptor.MetricDescriptorType.GAUGE_INT64,
        label_keys=[label_key.LabelKey('key', 'description')]
    )
    mm = metric.Metric(descriptor=desc, time_series=ts)
    return mm


class TestAzureMetricsExporter(unittest.TestCase):

    def setUp(self):
        os.environ["APPLICATIONINSIGHTS_STATSBEAT_DISABLED_ALL"] = "true"
        return super(TestAzureMetricsExporter, self).setUp()

    def tearDown(self):
        del os.environ["APPLICATIONINSIGHTS_STATSBEAT_DISABLED_ALL"]
        return super(TestAzureMetricsExporter, self).tearDown()

    def test_constructor_missing_key(self):
        self.assertRaises(ValueError, lambda: MetricsExporter(connection_string="", instrumentation_key=""))  # noqa: E501

    def test_constructor_invalid_batch_size(self):
        self.assertRaises(
            ValueError,
            lambda: MetricsExporter(
                instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
                max_batch_size=-1
            ))

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_export_metrics(self, requests_mock):
        metric = create_metric()
        exporter = MetricsExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd')
        requests_mock.return_value.text = '{"itemsReceived":1,'\
                                          '"itemsAccepted":1,'\
                                          '"errors":[]}'
        requests_mock.return_value.status_code = 200
        exporter.export_metrics([metric])

        self.assertEqual(len(requests_mock.call_args_list), 1)
        post_body = requests_mock.call_args_list[0][1]['data']
        self.assertTrue('metrics' in post_body)
        self.assertTrue('properties' in post_body)

    def test_export_metrics_histogram(self):
        metric = create_metric()
        exporter = MetricsExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd')
        metric.descriptor._type = MetricDescriptorType.CUMULATIVE_DISTRIBUTION

        self.assertIsNone(exporter.export_metrics([metric]))

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_export_metrics_empty(self, requests_mock):
        exporter = MetricsExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            max_batch_size=1,
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        exporter.export_metrics([])

        self.assertEqual(len(requests_mock.call_args_list), 0)
        self.assertEqual(len(os.listdir(exporter.storage.path)), 0)

    def test_export_metrics_retry(self):
        metric = create_metric()
        exporter = MetricsExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            max_batch_size=1,
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        with mock.patch('opencensus.ext.azure.metrics_exporter'
                        '.MetricsExporter._transmit') as transmit:
            transmit.return_value = TransportStatusCode.RETRY
            exporter.export_metrics([metric])

        self.assertEqual(len(os.listdir(exporter.storage.path)), 1)
        self.assertIsNone(exporter.storage.get())

    def test_export_metrics_success(self):
        metric = create_metric()
        exporter = MetricsExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            max_batch_size=1,
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        with mock.patch('opencensus.ext.azure.metrics_exporter'
                        '.MetricsExporter._transmit') as transmit:
            transmit.return_value = TransportStatusCode.SUCCESS
            exporter.export_metrics([metric])

        self.assertEqual(len(os.listdir(exporter.storage.path)), 0)
        self.assertIsNone(exporter.storage.get())

    def test_metric_to_envelopes(self):
        metric = create_metric()
        exporter = MetricsExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd'
        )
        property_mock = mock.Mock()
        envelope_mock = mock.Mock()
        exporter._create_properties = property_mock
        exporter._create_envelope = envelope_mock
        exporter.metric_to_envelopes(metric)
        property_mock.assert_called_once()
        envelope_mock.assert_called_once()

    def test_metric_to_envelopes_multi_time_series(self):
        metric = create_metric_ts()
        exporter = MetricsExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd'
        )
        property_mock = mock.Mock()
        envelope_mock = mock.Mock()
        exporter._create_properties = property_mock
        exporter._create_envelope = envelope_mock
        exporter.metric_to_envelopes(metric)
        property_mock.assert_any_call(
            metric.time_series[0],
            metric.descriptor.label_keys,
        )
        property_mock.assert_any_call(
            metric.time_series[1],
            metric.descriptor.label_keys,
        )
        envelope_mock.assert_called()

    def test_metric_to_envelopes_network_statsbeat(self):
        metric = create_stats_metric(_REQ_SUCCESS_NAME, 10)
        exporter = MetricsExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd'
        )
        statsbeat_mock = mock.Mock()
        statsbeat_mock.return_value = True
        property_mock = mock.Mock()
        envelope_mock = mock.Mock()
        exporter._create_properties = property_mock
        exporter._create_envelope = envelope_mock
        exporter._is_stats_exporter = statsbeat_mock
        exporter.metric_to_envelopes(metric)
        property_mock.assert_called_once()
        envelope_mock.assert_called_once()

    def test_metric_to_envelopes_network_statsbeat_zero(self):
        metric = create_stats_metric(_REQ_SUCCESS_NAME, 0)
        exporter = MetricsExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd'
        )
        statsbeat_mock = mock.Mock()
        statsbeat_mock.return_value = True
        property_mock = mock.Mock()
        envelope_mock = mock.Mock()
        exporter._create_properties = property_mock
        exporter._create_envelope = envelope_mock
        exporter._is_stats_exporter = statsbeat_mock
        exporter.metric_to_envelopes(metric)
        property_mock.assert_not_called()
        envelope_mock.assert_not_called()

    def test_metric_to_envelopes_not_network_statsbeat(self):
        metric = create_stats_metric(_ATTACH_METRIC_NAME, 10)
        exporter = MetricsExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd'
        )
        statsbeat_mock = mock.Mock()
        statsbeat_mock.return_value = True
        property_mock = mock.Mock()
        envelope_mock = mock.Mock()
        exporter._create_properties = property_mock
        exporter._create_envelope = envelope_mock
        exporter._is_stats_exporter = statsbeat_mock
        exporter.metric_to_envelopes(metric)
        property_mock.assert_called_once()
        envelope_mock.assert_called_once()

    def test_metric_to_envelopes_not_network_statsbeat_zero(self):
        metric = create_stats_metric(_ATTACH_METRIC_NAME, 0)
        exporter = MetricsExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd'
        )
        statsbeat_mock = mock.Mock()
        statsbeat_mock.return_value = True
        property_mock = mock.Mock()
        envelope_mock = mock.Mock()
        exporter._create_properties = property_mock
        exporter._create_envelope = envelope_mock
        exporter._is_stats_exporter = statsbeat_mock
        exporter.metric_to_envelopes(metric)
        property_mock.assert_called_once()
        envelope_mock.assert_called_once()

    def test_create_properties(self):
        metric = create_metric()
        exporter = MetricsExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd'
        )
        properties = exporter._create_properties(metric.time_series[0],
                                                 metric.descriptor.label_keys)

        self.assertEqual(len(properties), 1)
        self.assertEqual(properties['key'], 'val')

    def test_create_properties_none(self):
        metric = create_metric()
        exporter = MetricsExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd'
        )
        metric.time_series[0].label_values[0]._value = None
        properties = exporter._create_properties(metric.time_series[0],
                                                 metric.descriptor.label_keys)

        self.assertEqual(len(properties), 1)
        self.assertEqual(properties['key'], 'null')

    def test_create_envelope(self):
        metric = create_metric()
        exporter = MetricsExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd'
        )
        value = metric.time_series[0].points[0].value.value
        data_point = DataPoint(ns=metric.descriptor.name,
                               name=metric.descriptor.name,
                               value=value)
        timestamp = datetime(2019, 3, 20, 21, 34, 0, 537954)
        properties = {'url': 'website.com'}
        envelope = exporter._create_envelope(data_point, timestamp, properties)

        self.assertTrue('iKey' in envelope)
        self.assertEqual(envelope.iKey, '12345678-1234-5678-abcd-12345678abcd')
        self.assertTrue('tags' in envelope)
        self.assertTrue('time' in envelope)
        self.assertEqual(envelope.time, timestamp.isoformat())
        self.assertTrue('name' in envelope)
        self.assertEqual(envelope.name, 'Microsoft.ApplicationInsights.Metric')
        self.assertTrue('data' in envelope)
        self.assertTrue('baseData' in envelope.data)
        self.assertTrue('baseType' in envelope.data)
        self.assertTrue('metrics' in envelope.data.baseData)
        self.assertTrue('properties' in envelope.data.baseData)
        self.assertEqual(envelope.data.baseData.properties, properties)

    def test_shutdown(self):
        mock_thread = mock.Mock()
        mock_storage = mock.Mock()
        exporter = MetricsExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd'
        )
        exporter.exporter_thread = mock_thread
        exporter.storage = mock_storage
        exporter.shutdown()
        mock_thread.close.assert_called_once()
        mock_storage.close.assert_called_once()

    def test_shutdown_statsbeat(self):
        mock_thread = mock.Mock()
        mock_storage = mock.Mock()
        exporter = MetricsExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd'
        )
        exporter.exporter_thread = mock_thread
        exporter._is_stats = True
        exporter.storage = mock_storage
        exporter.shutdown()
        mock_thread.cancel.assert_called_once()
        mock_storage.close.assert_called_once()

    @mock.patch('opencensus.ext.azure.metrics_exporter'
                '.transport.get_exporter_thread')
    def test_new_metrics_exporter(self, exporter_mock):
        with mock.patch('opencensus.ext.azure.statsbeat'
                        '.statsbeat.collect_statsbeat_metrics') as hb:
            hb.return_value = None
            iKey = '12345678-1234-5678-abcd-12345678abcd'
            exporter = new_metrics_exporter(instrumentation_key=iKey)

            self.assertEqual(exporter.options.instrumentation_key, iKey)
            self.assertEqual(len(exporter_mock.call_args_list), 1)
            self.assertEqual(len(exporter_mock.call_args[0][0]), 2)
            producer_class = standard_metrics.AzureStandardMetricsProducer
            self.assertFalse(isinstance(exporter_mock.call_args[0][0][0],
                                        producer_class))
            self.assertTrue(isinstance(exporter_mock.call_args[0][0][1],
                                       producer_class))

    @mock.patch('opencensus.ext.azure.metrics_exporter'
                '.transport.get_exporter_thread')
    def test_new_metrics_exporter_no_standard_metrics(self, exporter_mock):
        with mock.patch('opencensus.ext.azure.statsbeat'
                        '.statsbeat.collect_statsbeat_metrics') as hb:
            hb.return_value = None
            iKey = '12345678-1234-5678-abcd-12345678abcd'
            exporter = new_metrics_exporter(
                instrumentation_key=iKey, enable_standard_metrics=False)

            self.assertEqual(exporter.options.instrumentation_key, iKey)
            self.assertEqual(len(exporter_mock.call_args_list), 1)
            self.assertEqual(len(exporter_mock.call_args[0][0]), 1)
            producer_class = standard_metrics.AzureStandardMetricsProducer
            self.assertFalse(isinstance(exporter_mock.call_args[0][0][0],
                                        producer_class))
