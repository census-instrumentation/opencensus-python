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

import json
import os
import platform
import unittest

import mock
import requests

from opencensus.metrics.export.gauge import LongGauge
from opencensus.ext.azure.common.utils import azure_monitor_context
from opencensus.ext.azure.metrics_exporter import statsbeat_metrics
from opencensus.ext.azure.metrics_exporter.statsbeat_metrics.statsbeat import (
    _get_attach_properties,
    _RP_NAMES,
    _StatsbeatMetrics,
)

class MockResponse(object):
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text


def throw(exc_type, *args, **kwargs):
    def func(*_args, **_kwargs):
        raise exc_type(*args, **kwargs)
    return func


class TestStatsbeatMetrics(unittest.TestCase):
    def setUp(self):
        # pylint: disable=protected-access
        statsbeat_metrics._STATSBEAT_METRICS = None

    def test_producer_ctor(self):
        # pylint: disable=protected-access
        producer = statsbeat_metrics._AzureStatsbeatMetricsProducer("ikey")
        metrics = producer._statsbeat
        self.assertTrue(
            isinstance(
                metrics,
                _StatsbeatMetrics
            )
        )
        self.assertEqual(metrics._instrumentation_key, "ikey")

    def test_producer_get_metrics(self):
        # pylint: disable=protected-access
        producer = statsbeat_metrics._AzureStatsbeatMetricsProducer("ikey")
        mock_stats = mock.Mock()
        producer._statsbeat = mock_stats
        producer.get_metrics()

        mock_stats.get_metrics.assert_called_once()

    @mock.patch('opencensus.metrics.transport.get_exporter_thread')
    def test_enable_statsbeat_metrics(self, exporter_mock):
        ikey = '12345678-1234-5678-abcd-12345678abcd'
        # pylint: disable=protected-access
        self.assertIsNone(statsbeat_metrics._STATSBEAT_METRICS)
        statsbeat_metrics.enable_statsbeat_metrics(None, ikey)
        self.assertTrue(
            isinstance(
                statsbeat_metrics._STATSBEAT_METRICS,
                statsbeat_metrics._AzureStatsbeatMetricsProducer
            )
        )
        exporter_mock.assert_called()

    @mock.patch('opencensus.metrics.transport.get_exporter_thread')
    def test_enable_statsbeat_metrics_exists(self, exporter_mock):
        # pylint: disable=protected-access
        producer = statsbeat_metrics._AzureStatsbeatMetricsProducer("ikey")
        statsbeat_metrics._STATSBEAT_METRICS = producer
        statsbeat_metrics.enable_statsbeat_metrics(None, None)
        self.assertEqual(statsbeat_metrics._STATSBEAT_METRICS, producer)
        exporter_mock.assert_not_called()

    @mock.patch('opencensus.ext.azure.metrics_exporter.statsbeat_metrics.statsbeat._get_attach_properties')
    def test_statsbeat_metric_init(self, attach_mock):
        # pylint: disable=protected-access
        metric = _StatsbeatMetrics("ikey")
        self.assertEqual(len(metric.vm_data), 0)
        self.assertTrue(metric.vm_retry)
        self.assertEqual(metric._instrumentation_key, "ikey")
        self.assertTrue(
            isinstance(
                metric._attach_metric,
                LongGauge,
            )
        )
        attach_mock.assert_called_once()

    def test_get_attach_properties(self):
        properties = _get_attach_properties()
        self.assertEqual(properties[0].key, "rp")
        self.assertEqual(properties[1].key, "rpid")
        self.assertEqual(properties[2].key, "attach")
        self.assertEqual(properties[3].key, "cikey")
        self.assertEqual(properties[4].key, "runtimeVersion")
        self.assertEqual(properties[5].key, "os")
        self.assertEqual(properties[6].key, "language")
        self.assertEqual(properties[7].key, "version")

    def test_statsbeat_metric_get_metrics(self):
        # pylint: disable=protected-access
        metric = statsbeat_metrics._StatsbeatMetrics("ikey")
        attach_metric_mock = mock.Mock()
        metric._get_attach_metric = attach_metric_mock
        metric.get_metrics()
        attach_metric_mock.assert_called_once()

    @mock.patch.dict(
        os.environ,
        {
            "WEBSITE_SITE_NAME": "site_name",
            "WEBSITE_HOME_STAMPNAME": "stamp_name",
        }
    )
    def test_statsbeat_metric_get_attach_metric_appsvc(self):
        # pylint: disable=protected-access
        stats = _StatsbeatMetrics("ikey")
        metric = stats._get_attach_metric(stats._attach_metric)
        properties = metric._time_series[0]._label_values
        self.assertEqual(len(properties), 8)
        self.assertEqual(properties[0].value, _RP_NAMES[1])
        self.assertEqual(properties[1].value, "site_name/stamp_name")
        self.assertEqual(properties[2].value, "sdk")
        self.assertEqual(properties[3].value, "ikey")
        self.assertEqual(properties[4].value, platform.python_version())
        self.assertEqual(properties[5].value, platform.system())
        self.assertEqual(properties[6].value, "python")
        self.assertEqual(properties[7].value, azure_monitor_context["ai.internal.sdkVersion"])

    @mock.patch.dict(
        os.environ,
        {
            "FUNCTIONS_WORKER_RUNTIME": "runtime",
            "WEBSITE_HOSTNAME": "host_name",
        }
    )
    def test_statsbeat_metric_get_attach_metric_function(self):
        # pylint: disable=protected-access
        stats = _StatsbeatMetrics("ikey")
        metric = stats._get_attach_metric(stats._attach_metric)
        properties = metric._time_series[0]._label_values
        self.assertEqual(len(properties), 8)
        self.assertEqual(properties[0].value, _RP_NAMES[2])
        self.assertEqual(properties[1].value, "host_name")
        self.assertEqual(properties[2].value, "sdk")
        self.assertEqual(properties[3].value, "ikey")
        self.assertEqual(properties[4].value, platform.python_version())
        self.assertEqual(properties[5].value, platform.system())
        self.assertEqual(properties[6].value, "python")
        self.assertEqual(properties[7].value, azure_monitor_context["ai.internal.sdkVersion"])


    # def test_heartbeat_metric_init_vm(self):
    #     with mock.patch('requests.get') as get:
    #         get.return_value = MockResponse(
    #             200,
    #             json.dumps(
    #                 {
    #                     'vmId': 5,
    #                     'subscriptionId': 3,
    #                     'osType': 'Linux'
    #                 }
    #             )
    #         )
    #         metric = heartbeat_metrics.HeartbeatMetric()
    #         self.assertFalse(metric.init)
    #         self.assertFalse(metric.vm_retry)
    #         metric.get_metrics()
    #         self.assertTrue(metric.init)
    #         self.assertFalse(metric.vm_retry)
    #         self.assertEqual(metric.NAME, 'Heartbeat')
    #         keys = list(metric.properties.keys())
    #         values = list(metric.properties.values())
    #         self.assertEqual(len(keys), 5)
    #         self.assertEqual(len(keys), len(values))
    #         self.assertEqual(keys[0].key, "sdk")
    #         self.assertEqual(keys[1].key, "osType")
    #         self.assertEqual(values[0].value, 'py{}:oc{}:ext{}'.format(
    #             platform.python_version(),
    #             opencensus_version,
    #             ext_version,
    #         ))
    #         self.assertEqual(values[1].value, platform.system())
    #         self.assertEqual(keys[2].key, "azInst_vmId")
    #         self.assertEqual(values[2].value, 5)
    #         self.assertEqual(keys[3].key, "azInst_subscriptionId")
    #         self.assertEqual(values[3].value, 3)
    #         self.assertEqual(keys[4].key, "azInst_osType")
    #         self.assertEqual(values[4].value, "Linux")

    # def test_heartbeat_metric_not_vm(self):
    #     with mock.patch(
    #         'requests.get',
    #         throw(requests.exceptions.ConnectionError)
    #     ):
    #         metric = heartbeat_metrics.HeartbeatMetric()
    #         self.assertFalse(metric.init)
    #         self.assertFalse(metric.vm_retry)
    #         metric.get_metrics()
    #         self.assertTrue(metric.init)
    #         self.assertFalse(metric.vm_retry)
    #         self.assertEqual(metric.NAME, 'Heartbeat')
    #         keys = list(metric.properties.keys())
    #         self.assertEqual(len(keys), 2)

    # def test_heartbeat_metric_not_vm_timeout(self):
    #     with mock.patch(
    #         'requests.get',
    #         throw(requests.Timeout)
    #     ):
    #         metric = heartbeat_metrics.HeartbeatMetric()
    #         self.assertFalse(metric.init)
    #         self.assertFalse(metric.vm_retry)
    #         metric.get_metrics()
    #         self.assertTrue(metric.init)
    #         self.assertFalse(metric.vm_retry)
    #         self.assertEqual(metric.NAME, 'Heartbeat')
    #         keys = list(metric.properties.keys())
    #         self.assertEqual(len(keys), 2)

    # def test_heartbeat_metric_vm_retry(self):
    #     with mock.patch(
    #         'requests.get',
    #         throw(requests.exceptions.RequestException)
    #     ):
    #         metric = heartbeat_metrics.HeartbeatMetric()
    #         self.assertFalse(metric.init)
    #         self.assertFalse(metric.vm_retry)
    #         metric.get_metrics()
    #         self.assertTrue(metric.init)
    #         self.assertTrue(metric.vm_retry)
    #         keys = list(metric.properties.keys())
    #         self.assertEqual(len(keys), 2)
    #         self.assertEqual(len(metric.vm_data), 0)
    #         with mock.patch('requests.get') as get:
    #             get.return_value = MockResponse(
    #                 200,
    #                 json.dumps(
    #                     {
    #                         'vmId': 5,
    #                         'subscriptionId': 3,
    #                         'osType': 'Linux'
    #                     }
    #                 )
    #             )
    #             metric.get_metrics()
    #             self.assertFalse(metric.vm_retry)
    #             self.assertEqual(len(metric.vm_data), 3)
    #             keys = list(metric.properties.keys())
    #             self.assertEqual(len(keys), 5)
