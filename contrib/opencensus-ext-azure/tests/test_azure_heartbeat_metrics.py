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

from opencensus.common.version import __version__ as opencensus_version
from opencensus.ext.azure.common.version import __version__ as ext_version
from opencensus.ext.azure.metrics_exporter import heartbeat_metrics


class MockResponse(object):
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text


def throw(exc_type, *args, **kwargs):
    def func(*_args, **_kwargs):
        raise exc_type(*args, **kwargs)
    return func


class TestHeartbeatMetrics(unittest.TestCase):
    def setUp(self):
        # pylint: disable=protected-access
        heartbeat_metrics._HEARTBEAT_METRICS = None

    def test_producer_ctor(self):
        producer = heartbeat_metrics.AzureHeartbeatMetricsProducer()
        # pylint: disable=protected-access
        metric = producer._heartbeat
        self.assertTrue(
            isinstance(
                metric,
                heartbeat_metrics.heartbeat.HeartbeatMetric
            )
        )

    def test_producer_get_metrics(self):
        producer = heartbeat_metrics.AzureHeartbeatMetricsProducer()
        metrics = producer.get_metrics()

        self.assertEqual(len(metrics), 1)

    @mock.patch('opencensus.metrics.transport.get_exporter_thread')
    def test_enable_heartbeat_metrics(self, transport_mock):
        ikey = '12345678-1234-5678-abcd-12345678abcd'
        # pylint: disable=protected-access
        self.assertIsNone(heartbeat_metrics._HEARTBEAT_METRICS)
        heartbeat_metrics.enable_heartbeat_metrics(None, ikey)
        self.assertTrue(
            isinstance(
                heartbeat_metrics._HEARTBEAT_METRICS,
                heartbeat_metrics.AzureHeartbeatMetricsProducer
            )
        )
        transport_mock.assert_called()

    @mock.patch('opencensus.metrics.transport.get_exporter_thread')
    def test_enable_heartbeat_metrics_exists(self, transport_mock):
        # pylint: disable=protected-access
        producer = heartbeat_metrics.AzureHeartbeatMetricsProducer()
        heartbeat_metrics._HEARTBEAT_METRICS = producer
        heartbeat_metrics.enable_heartbeat_metrics(None, None)
        self.assertEqual(heartbeat_metrics._HEARTBEAT_METRICS, producer)
        transport_mock.assert_not_called()

    def test_heartbeat_metric_init(self):
        metric = heartbeat_metrics.HeartbeatMetric()
        self.assertEqual(len(metric.vm_data), 0)
        self.assertFalse(metric.vm_retry)
        self.assertFalse(metric.init)
        self.assertEqual(len(metric.properties), 0)

    def test_heartbeat_metric_get_metric_init(self):
        metric = heartbeat_metrics.HeartbeatMetric()
        self.assertFalse(metric.init)
        metrics = metric.get_metrics()
        self.assertTrue(metric.init)
        self.assertEqual(metric.NAME, 'Heartbeat')
        keys = list(metric.properties.keys())
        values = list(metric.properties.values())
        self.assertEqual(len(keys), 5)
        self.assertEqual(len(keys), len(values))
        self.assertEqual(keys[0].key, "sdk")
        self.assertEqual(keys[1].key, "osType")
        self.assertEqual(values[0].value, 'py{}:oc{}:ext{}'.format(
            platform.python_version(),
            opencensus_version,
            ext_version,
        ))
        self.assertEqual(values[1].value, platform.system())
        gauge = metric.heartbeat

        self.assertEqual(gauge.descriptor.name, 'Heartbeat')
        self.assertEqual(
            gauge.descriptor.description,
            'Heartbeat metric with custom dimensions'
        )
        self.assertEqual(gauge.descriptor.unit, 'count')
        self.assertEqual(gauge.descriptor._type, 1)
        self.assertEqual(
            gauge.descriptor.label_keys,
            list(metric.properties.keys())
        )
        self.assertEqual(
            gauge._len_label_keys,
            len(metric.properties.keys())
        )
        self.assertEqual(len(metrics), 1)

    @mock.patch.dict(
        os.environ,
        {
            "WEBSITE_SITE_NAME": "site_name",
            "WEBSITE_HOME_STAMPNAME": "stamp_name",
            "WEBSITE_HOSTNAME": "host_name",
        }
    )
    def test_heartbeat_metric_init_webapp(self):
        metric = heartbeat_metrics.HeartbeatMetric()
        self.assertFalse(metric.init)
        metric.get_metrics()
        self.assertTrue(metric.init)
        self.assertEqual(metric.NAME, 'Heartbeat')
        keys = list(metric.properties.keys())
        values = list(metric.properties.values())
        self.assertEqual(len(keys), 5)
        self.assertEqual(len(keys), len(values))
        self.assertEqual(keys[0].key, "sdk")
        self.assertEqual(keys[1].key, "osType")
        self.assertEqual(values[0].value, 'py{}:oc{}:ext{}'.format(
            platform.python_version(),
            opencensus_version,
            ext_version,
        ))
        self.assertEqual(values[1].value, platform.system())
        self.assertEqual(keys[2].key, "appSrv_SiteName")
        self.assertEqual(keys[3].key, "appSrv_wsStamp")
        self.assertEqual(keys[4].key, "appSrv_wsHost")
        self.assertEqual(values[2].value, "site_name")
        self.assertEqual(values[3].value, "stamp_name")
        self.assertEqual(values[4].value, "host_name")

    @mock.patch.dict(
        os.environ,
        {
            "FUNCTIONS_WORKER_RUNTIME": "python",
            "WEBSITE_HOSTNAME": "host_name",
        }
    )
    def test_heartbeat_metric_init_functionapp(self):
        metric = heartbeat_metrics.HeartbeatMetric()
        self.assertFalse(metric.init)
        metric.get_metrics()
        self.assertTrue(metric.init)
        self.assertEqual(metric.NAME, 'Heartbeat')
        keys = list(metric.properties.keys())
        values = list(metric.properties.values())
        self.assertEqual(len(keys), 3)
        self.assertEqual(len(keys), len(values))
        self.assertEqual(keys[0].key, "sdk")
        self.assertEqual(keys[1].key, "osType")
        self.assertEqual(values[0].value, 'py{}:oc{}:ext{}'.format(
            platform.python_version(),
            opencensus_version,
            ext_version,
        ))
        self.assertEqual(values[1].value, platform.system())
        self.assertEqual(keys[2].key, "azfunction_appId")
        self.assertEqual(values[2].value, "host_name")

    def test_heartbeat_metric_init_vm(self):
        with mock.patch('requests.get') as get:
            get.return_value = MockResponse(
                200,
                json.dumps(
                    {
                        'vmId': 5,
                        'subscriptionId': 3,
                        'osType': 'Linux'
                    }
                )
            )
            metric = heartbeat_metrics.HeartbeatMetric()
            self.assertFalse(metric.init)
            self.assertFalse(metric.vm_retry)
            metric.get_metrics()
            self.assertTrue(metric.init)
            self.assertFalse(metric.vm_retry)
            self.assertEqual(metric.NAME, 'Heartbeat')
            keys = list(metric.properties.keys())
            values = list(metric.properties.values())
            self.assertEqual(len(keys), 5)
            self.assertEqual(len(keys), len(values))
            self.assertEqual(keys[0].key, "sdk")
            self.assertEqual(keys[1].key, "osType")
            self.assertEqual(values[0].value, 'py{}:oc{}:ext{}'.format(
                platform.python_version(),
                opencensus_version,
                ext_version,
            ))
            self.assertEqual(values[1].value, platform.system())
            self.assertEqual(keys[2].key, "azInst_vmId")
            self.assertEqual(values[2].value, 5)
            self.assertEqual(keys[3].key, "azInst_subscriptionId")
            self.assertEqual(values[3].value, 3)
            self.assertEqual(keys[4].key, "azInst_osType")
            self.assertEqual(values[4].value, "Linux")

    def test_heartbeat_metric_not_vm(self):
        with mock.patch(
            'requests.get',
            throw(requests.exceptions.ConnectionError)
        ):
            metric = heartbeat_metrics.HeartbeatMetric()
            self.assertFalse(metric.init)
            self.assertFalse(metric.vm_retry)
            metric.get_metrics()
            self.assertTrue(metric.init)
            self.assertFalse(metric.vm_retry)
            self.assertEqual(metric.NAME, 'Heartbeat')
            keys = list(metric.properties.keys())
            self.assertEqual(len(keys), 2)

    def test_heartbeat_metric_not_vm_timeout(self):
        with mock.patch(
            'requests.get',
            throw(requests.Timeout)
        ):
            metric = heartbeat_metrics.HeartbeatMetric()
            self.assertFalse(metric.init)
            self.assertFalse(metric.vm_retry)
            metric.get_metrics()
            self.assertTrue(metric.init)
            self.assertFalse(metric.vm_retry)
            self.assertEqual(metric.NAME, 'Heartbeat')
            keys = list(metric.properties.keys())
            self.assertEqual(len(keys), 2)

    def test_heartbeat_metric_vm_retry(self):
        with mock.patch(
            'requests.get',
            throw(requests.exceptions.RequestException)
        ):
            metric = heartbeat_metrics.HeartbeatMetric()
            self.assertFalse(metric.init)
            self.assertFalse(metric.vm_retry)
            metric.get_metrics()
            self.assertTrue(metric.init)
            self.assertTrue(metric.vm_retry)
            keys = list(metric.properties.keys())
            self.assertEqual(len(keys), 2)
            self.assertEqual(len(metric.vm_data), 0)
            with mock.patch('requests.get') as get:
                get.return_value = MockResponse(
                    200,
                    json.dumps(
                        {
                            'vmId': 5,
                            'subscriptionId': 3,
                            'osType': 'Linux'
                        }
                    )
                )
                metric.get_metrics()
                self.assertFalse(metric.vm_retry)
                self.assertEqual(len(metric.vm_data), 3)
                keys = list(metric.properties.keys())
                self.assertEqual(len(keys), 5)
