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
import platform
import unittest

import mock

from opencensus.common.version import __version__ as opencensus_version
from opencensus.ext.azure.common.version import __version__ as ext_version
from opencensus.ext.azure.metrics_exporter import heartbeat_metrics
from opencensus.metrics.label_key import LabelKey
from opencensus.metrics.label_value import LabelValue


class TestHeartbeatMetrics(unittest.TestCase):
    def setUp(self):
        # pylint: disable=protected-access
        heartbeat_metrics._HEARTBEAT_METRICS = None


    @mock.patch('opencensus.ext.azure.metrics_exporter'
                '.heartbeat_metrics.register_metrics')
    def test_producer_ctor(self, avail_mock):
        heartbeat_metrics.AzureHeartbeatMetricsProducer()

        self.assertEqual(len(avail_mock.call_args_list), 1)

    def test_producer_get_metrics(self):
        producer = heartbeat_metrics.AzureHeartbeatMetricsProducer()
        metrics = producer.get_metrics()

        self.assertEqual(len(metrics), 1)

    def test_register_metrics(self):
        registry = heartbeat_metrics.register_metrics()

        self.assertEqual(len(registry.get_metrics()), 1)

    @mock.patch('opencensus.metrics.transport.get_exporter_thread')
    def test_enable_heartbeat_metrics(self, transport_mock):
        ikey = '12345678-1234-5678-abcd-12345678abcd'
        # pylint: disable=protected-access
        self.assertIsNone(heartbeat_metrics._HEARTBEAT_METRICS)
        heartbeat_metrics.enable_heartbeat_metrics(None, ikey)
        self.assertTrue(isinstance(heartbeat_metrics._HEARTBEAT_METRICS,
                                   heartbeat_metrics.AzureHeartbeatMetricsProducer))
        transport_mock.assert_called()

    @mock.patch('opencensus.metrics.transport.get_exporter_thread')
    def test_enable_heartbeat_metrics_exits(self, transport_mock):
        # pylint: disable=protected-access
        producer = heartbeat_metrics.AzureHeartbeatMetricsProducer()
        heartbeat_metrics._HEARTBEAT_METRICS = producer
        heartbeat_metrics.enable_heartbeat_metrics(None, None)
        self.assertEqual(heartbeat_metrics._HEARTBEAT_METRICS, producer)
        transport_mock.assert_not_called()

    def test_heartbeat_metric_init(self):
        metric = heartbeat_metrics.HeartbeatMetric()

        self.assertEqual(metric.NAME, 'Heartbeat')
        keys = list(metric.properties.keys())
        values = list(metric.properties.values())
        self.assertEqual(len(keys), 2)
        self.assertEqual(len(keys), len(values))
        self.assertEqual(keys[0].key, "sdk")
        self.assertEqual(keys[1].key, "osType")
        self.assertEqual(values[0].value, 'py{}:oc{}:ext{}'.format(
                platform.python_version(),
                opencensus_version,
                ext_version,
            ))
        self.assertEqual(values[1].value, platform.system())

    @mock.patch.dict(os.environ,
        {
            "WEBSITE_SITE_NAME": "site_name",
            "WEBSITE_HOME_STAMPNAME": "stamp_name",
            "WEBSITE_HOSTNAME": "host_name",
        }
    )
    def test_heartbeat_metric_init_webapp(self):
        metric = heartbeat_metrics.HeartbeatMetric()

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

    @mock.patch.dict(os.environ,
        {
            "FUNCTIONS_WORKER_RUNTIME": "python",
            "WEBSITE_HOSTNAME": "host_name",
        }
    )
    def test_heartbeat_metric_init_functionapp(self):
        metric = heartbeat_metrics.HeartbeatMetric()

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
 
    def test_heartbeat_metric(self):
        metric = heartbeat_metrics.HeartbeatMetric()
        gauge = metric()

        self.assertEqual(gauge.descriptor.name, 'Heartbeat')
        self.assertEqual(gauge.descriptor.description,
            'Heartbeat metric with custom dimensions')
        self.assertEqual(gauge.descriptor.unit, 'count')
        self.assertEqual(gauge.descriptor._type, 1)
        self.assertEqual(gauge.descriptor.label_keys,
            list(metric.properties.keys()))
        self.assertEqual(gauge._len_label_keys,
            len(metric.properties.keys()))
