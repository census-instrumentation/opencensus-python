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

import mock
import unittest
from datetime import datetime

from opencensus.common import utils
from opencensus.ext.azure import metrics_exporter
from opencensus.ext.azure.common import Options
from opencensus.ext.azure.common.protocol import DataPoint
from opencensus.metrics import label_key
from opencensus.metrics import label_value
from opencensus.metrics.export import metric
from opencensus.metrics.export import metric_descriptor
from opencensus.metrics.export import point
from opencensus.metrics.export import time_series
from opencensus.metrics.export import value
from opencensus.metrics.export.metric_descriptor import MetricDescriptorType


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


class TestAzureMetricsExporter(unittest.TestCase):
    def setUp(self):
        self.options = Options(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd')

    def test_constructor_missing_key(self):
        instrumentation_key = Options._default.instrumentation_key
        Options._default.instrumentation_key = None
        self.assertRaises(ValueError,
                          lambda: metrics_exporter.MetricsExporter())
        Options._default.instrumentation_key = instrumentation_key

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_export_metrics(self, requests_mock):
        metric = create_metric()
        exporter = metrics_exporter.MetricsExporter(self.options)
        requests_mock.return_value.status_code = 200
        exporter.export_metrics([metric])

        self.assertEqual(len(requests_mock.call_args_list), 1)
        post_body = requests_mock.call_args_list[0][1]['data']
        self.assertTrue('metrics' in post_body)
        self.assertTrue('properties' in post_body)

    def test_export_metrics_histogram(self):
        metric = create_metric()
        metric.descriptor._type = MetricDescriptorType.CUMULATIVE_DISTRIBUTION
        exporter = metrics_exporter.MetricsExporter(self.options)

        self.assertIsNone(exporter.export_metrics([metric]))

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_export_metrics_empty(self, requests_mock):
        exporter = metrics_exporter.MetricsExporter(self.options)
        exporter.export_metrics([])

        self.assertEqual(len(requests_mock.call_args_list), 0)

    def test_create_data_points(self):
        metric = create_metric()
        exporter = metrics_exporter.MetricsExporter(self.options)
        data_points = exporter.create_data_points(metric.time_series[0],
                                                  metric.descriptor)

        self.assertEqual(len(data_points), 1)
        data_point = data_points[0]
        self.assertEqual(data_point.ns, metric.descriptor.name)
        self.assertEqual(data_point.name, metric.descriptor.name)
        self.assertEqual(data_point.value,
                         metric.time_series[0].points[0].value.value)

    def test_create_properties(self):
        metric = create_metric()
        exporter = metrics_exporter.MetricsExporter(self.options)
        properties = exporter.create_properties(metric.time_series[0],
                                                metric.descriptor)

        self.assertEqual(len(properties), 1)
        self.assertEqual(properties['key'], 'val')

    def test_create_properties_none(self):
        metric = create_metric()
        exporter = metrics_exporter.MetricsExporter(self.options)
        metric.time_series[0].label_values[0]._value = None
        properties = exporter.create_properties(metric.time_series[0],
                                                metric.descriptor)

        self.assertEqual(len(properties), 1)
        self.assertEqual(properties['key'], 'None')

    def test_create_envelope(self):
        metric = create_metric()
        exporter = metrics_exporter.MetricsExporter(self.options)
        value = metric.time_series[0].points[0].value.value
        data_point = DataPoint(ns=metric.descriptor.name,
                               name=metric.descriptor.name,
                               value=value)
        timestamp = datetime(2019, 3, 20, 21, 34, 0, 537954)
        properties = {'url': 'website.com'}
        envelope = exporter.create_envelope(data_point, timestamp, properties)

        self.assertTrue('iKey' in envelope)
        self.assertEqual(envelope.iKey, self.options.instrumentation_key)
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

    @mock.patch('opencensus.ext.azure.metrics_exporter' +
                '.transport.get_exporter_thread', return_value=mock.Mock())
    def test_new_metrics_exporter(self, exporter_mock):
        iKey = '12345678-1234-5678-abcd-12345678abcd'
        exporter = metrics_exporter.new_metrics_exporter(
            instrumentation_key=iKey)

        self.assertEqual(exporter.options.instrumentation_key, iKey)