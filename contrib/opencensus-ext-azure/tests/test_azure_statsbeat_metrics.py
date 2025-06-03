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

from opencensus.ext.azure.common import Options
from opencensus.ext.azure.common.transport import _requests_map
from opencensus.ext.azure.common.version import __version__ as ext_version
from opencensus.ext.azure.metrics_exporter import MetricsExporter
from opencensus.ext.azure.statsbeat import statsbeat
from opencensus.ext.azure.statsbeat.statsbeat_metrics import (
    _DEFAULT_EU_STATS_CONNECTION_STRING,
    _DEFAULT_NON_EU_STATS_CONNECTION_STRING,
    _ENDPOINT_TYPES,
    _FEATURE_TYPES,
    _REQ_DURATION_NAME,
    _REQ_EXCEPTION_NAME,
    _REQ_FAILURE_NAME,
    _REQ_RETRY_NAME,
    _REQ_SUCCESS_NAME,
    _REQ_THROTTLE_NAME,
    _RP_NAMES,
    _STATS_LONG_INTERVAL_THRESHOLD,
    _get_attach_properties,
    _get_average_duration_value,
    _get_common_properties,
    _get_exception_count_value,
    _get_failure_count_value,
    _get_feature_properties,
    _get_network_properties,
    _get_retry_count_value,
    _get_stats_connection_string,
    _get_success_count_value,
    _get_throttle_count_value,
    _shorten_host,
    _StatsbeatMetrics,
)
from opencensus.metrics.export.gauge import (
    DerivedDoubleGauge,
    DerivedLongGauge,
    LongGauge,
)
from opencensus.trace import integrations

_OPTIONS = Options(
    instrumentation_key="ikey",
    enable_local_storage=True,
    endpoint="https://eastus-1.in.applicationinsights.azure.com/",
    credential=None,
)


class MockResponse(object):
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text


class MockCredential(object):
    def get_token():
        pass


def throw(exc_type, *args, **kwargs):
    def func(*_args, **_kwargs):
        raise exc_type(*args, **kwargs)
    return func


class TestStatsbeatMetrics(unittest.TestCase):
    def setUp(self):
        # pylint: disable=protected-access
        statsbeat._STATSBEAT_METRICS = None
        statsbeat._STATSBEAT_EXPORTER = None
        _STATSBEAT_STATE = {  # noqa: F841
            "INITIAL_FAILURE_COUNT": 0,
            "INITIAL_SUCCESS": False,
            "SHUTDOWN": False,
        }

    def test_producer_ctor(self):
        # pylint: disable=protected-access
        producer = statsbeat._AzureStatsbeatMetricsProducer(_OPTIONS)
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
        producer = statsbeat._AzureStatsbeatMetricsProducer(_OPTIONS)
        mock_stats = mock.Mock()
        producer._statsbeat = mock_stats
        producer.get_metrics()

        mock_stats.get_metrics.assert_called_once()

    def test_producer_get_initial_metrics(self):
        # pylint: disable=protected-access
        producer = statsbeat._AzureStatsbeatMetricsProducer(_OPTIONS)
        mock_stats = mock.Mock()
        producer._statsbeat = mock_stats
        producer.get_initial_metrics()

        mock_stats.get_initial_metrics.assert_called_once()

    @mock.patch.object(_StatsbeatMetrics, 'get_initial_metrics')
    @mock.patch('opencensus.metrics.transport.get_exporter_thread')
    def test_collect_statsbeat_metrics(self, thread_mock, stats_mock):
        # pylint: disable=protected-access
        self.assertIsNone(statsbeat._STATSBEAT_METRICS)
        statsbeat.collect_statsbeat_metrics(_OPTIONS)
        self.assertTrue(
            isinstance(
                statsbeat._STATSBEAT_METRICS,
                statsbeat._AzureStatsbeatMetricsProducer
            )
        )
        self.assertTrue(
            isinstance(
                statsbeat._STATSBEAT_EXPORTER,
                MetricsExporter,
            )
        )
        self.assertEqual(
            statsbeat._STATSBEAT_METRICS._statsbeat._instrumentation_key, "ikey")  # noqa: E501
        thread_mock.assert_called_once()
        stats_mock.assert_called_once()

    @mock.patch.object(_StatsbeatMetrics, 'get_initial_metrics')
    @mock.patch('opencensus.metrics.transport.get_exporter_thread')
    def test_collect_statsbeat_metrics_exists(self, thread_mock, stats_mock):
        # pylint: disable=protected-access
        self.assertIsNone(statsbeat._STATSBEAT_METRICS)
        producer = statsbeat._AzureStatsbeatMetricsProducer(_OPTIONS)
        statsbeat._STATSBEAT_METRICS = producer
        statsbeat.collect_statsbeat_metrics(None)
        self.assertEqual(statsbeat._STATSBEAT_METRICS, producer)
        thread_mock.assert_not_called()
        stats_mock.assert_not_called()

    @mock.patch.object(_StatsbeatMetrics, 'get_initial_metrics')
    @mock.patch('opencensus.metrics.transport.get_exporter_thread')
    def test_collect_statsbeat_metrics_non_eu(self, thread_mock, stats_mock):
        # pylint: disable=protected-access
        cs = "InstrumentationKey=1aa11111-bbbb-1ccc-8ddd-eeeeffff3333;IngestionEndpoint=https://westus-0.in.applicationinsights.azure.com/"  # noqa: E501
        non_eu = Options(
            connection_string=cs
        )
        self.assertIsNone(statsbeat._STATSBEAT_METRICS)
        with mock.patch.dict(
                os.environ, {
                    "APPLICATION_INSIGHTS_STATS_CONNECTION_STRING": "",
                }):
            statsbeat.collect_statsbeat_metrics(non_eu)
            self.assertTrue(
                isinstance(
                    statsbeat._STATSBEAT_METRICS,
                    statsbeat._AzureStatsbeatMetricsProducer
                )
            )
            self.assertTrue(
                isinstance(
                    statsbeat._STATSBEAT_EXPORTER,
                    MetricsExporter,
                )
            )
            self.assertEqual(
                statsbeat._STATSBEAT_EXPORTER.options.instrumentation_key,  # noqa: E501
                _DEFAULT_NON_EU_STATS_CONNECTION_STRING.split(";")[0].split("=")[1]   # noqa: E501
            )
            self.assertEqual(
                statsbeat._STATSBEAT_EXPORTER.options.endpoint,
                _DEFAULT_NON_EU_STATS_CONNECTION_STRING.split(";")[1].split("=")[1]   # noqa: E501
            )

    @mock.patch.object(_StatsbeatMetrics, 'get_initial_metrics')
    @mock.patch('opencensus.metrics.transport.get_exporter_thread')
    def test_collect_statsbeat_metrics_eu(self, thread_mock, stats_mock):
        # pylint: disable=protected-access
        cs = "InstrumentationKey=1aa11111-bbbb-1ccc-8ddd-eeeeffff3333;IngestionEndpoint=https://northeurope-0.in.applicationinsights.azure.com/"  # noqa: E501
        eu = Options(
            connection_string=cs
        )
        with mock.patch.dict(
                os.environ, {
                    "APPLICATION_INSIGHTS_STATS_CONNECTION_STRING": "",
                }):
            statsbeat.collect_statsbeat_metrics(eu)
            self.assertTrue(
                isinstance(
                    statsbeat._STATSBEAT_METRICS,
                    statsbeat._AzureStatsbeatMetricsProducer
                )
            )
            self.assertTrue(
                isinstance(
                    statsbeat._STATSBEAT_EXPORTER,
                    MetricsExporter,
                )
            )
            self.assertEqual(
                statsbeat._STATSBEAT_EXPORTER.options.instrumentation_key,  # noqa: E501
                _DEFAULT_EU_STATS_CONNECTION_STRING.split(";")[0].split("=")[1]   # noqa: E501
            )
            self.assertEqual(
                statsbeat._STATSBEAT_EXPORTER.options.endpoint,
                _DEFAULT_EU_STATS_CONNECTION_STRING.split(";")[1].split("=")[1]   # noqa: E501
            )

    def test_shutdown_statsbeat_metrics(self):
        # pylint: disable=protected-access
        producer_mock = mock.Mock()
        exporter_mock = mock.Mock()
        statsbeat._STATSBEAT_METRICS = producer_mock
        statsbeat._STATSBEAT_EXPORTER = exporter_mock
        statsbeat.shutdown_statsbeat_metrics()
        exporter_mock.shutdown.assert_called_once()
        self.assertIsNone(statsbeat._STATSBEAT_METRICS)
        self.assertIsNone(statsbeat._STATSBEAT_EXPORTER)

    def test_shutdown_statsbeat_metrics_already_shutdown(self):
        # pylint: disable=protected-access
        producer_mock = mock.Mock()
        exporter_mock = mock.Mock()
        statsbeat._STATSBEAT_METRICS = producer_mock
        statsbeat._STATSBEAT_EXPORTER = exporter_mock
        statsbeat._STATSBEAT_STATE["SHUTDOWN"] = True
        statsbeat.shutdown_statsbeat_metrics()
        exporter_mock.shutdown.assert_not_called()
        self.assertIsNotNone(statsbeat._STATSBEAT_METRICS)
        self.assertIsNotNone(statsbeat._STATSBEAT_EXPORTER)

    @mock.patch(
        'opencensus.ext.azure.statsbeat.statsbeat_metrics._get_feature_properties')  # noqa: E501
    @mock.patch(
        'opencensus.ext.azure.statsbeat.statsbeat_metrics._get_network_properties')  # noqa: E501
    @mock.patch(
        'opencensus.ext.azure.statsbeat.statsbeat_metrics._get_attach_properties')  # noqa: E501
    def test_statsbeat_metric_init(self, attach_mock, network_mock, feature_mock):  # noqa: E501
        # pylint: disable=protected-access
        metric = _StatsbeatMetrics(_OPTIONS)
        self.assertEqual(len(metric._vm_data), 0)
        self.assertTrue(metric._vm_retry)
        self.assertEqual(metric._instrumentation_key, "ikey")
        self.assertEqual(metric._feature, 1)
        self.assertTrue(
            isinstance(
                metric._attach_metric,
                LongGauge,
            )
        )
        self.assertTrue(
            isinstance(
                metric._network_metrics[_get_success_count_value],
                DerivedLongGauge,
            )
        )
        self.assertTrue(
            isinstance(
                metric._network_metrics[_get_failure_count_value],
                DerivedLongGauge,
            )
        )
        self.assertTrue(
            isinstance(
                metric._network_metrics[_get_average_duration_value],
                DerivedDoubleGauge,
            )
        )
        self.assertTrue(
            isinstance(
                metric._network_metrics[_get_retry_count_value],
                DerivedLongGauge,
            )
        )
        self.assertTrue(
            isinstance(
                metric._network_metrics[_get_throttle_count_value],
                DerivedLongGauge,
            )
        )
        self.assertTrue(
            isinstance(
                metric._network_metrics[_get_exception_count_value],
                DerivedLongGauge,
            )
        )
        self.assertTrue(
            isinstance(
                metric._feature_metric,
                LongGauge,
            )
        )
        self.assertTrue(
            isinstance(
                metric._instrumentation_metric,
                LongGauge,
            )
        )
        attach_mock.assert_called_once()
        network_mock.assert_called()
        self.assertEqual(feature_mock.call_count, 2)
        attach_mock.assert_called_once()
        network_mock.assert_called()
        self.assertEqual(network_mock.call_count, 6)

    def test_get_attach_properties(self):
        properties = _get_attach_properties()
        self.assertEqual(properties[0].key, "rp")
        self.assertEqual(properties[1].key, "rpId")
        self.assertEqual(properties[2].key, "attach")
        self.assertEqual(properties[3].key, "cikey")
        self.assertEqual(properties[4].key, "runtimeVersion")
        self.assertEqual(properties[5].key, "os")
        self.assertEqual(properties[6].key, "language")
        self.assertEqual(properties[7].key, "version")

    def test_get_feature_properties(self):
        properties = _get_feature_properties()
        self.assertEqual(properties[0].key, "rp")
        self.assertEqual(properties[1].key, "attach")
        self.assertEqual(properties[2].key, "cikey")
        self.assertEqual(properties[3].key, "runtimeVersion")
        self.assertEqual(properties[4].key, "type")
        self.assertEqual(properties[5].key, "feature")
        self.assertEqual(properties[6].key, "os")
        self.assertEqual(properties[7].key, "language")
        self.assertEqual(properties[8].key, "version")

    def test_get_network_properties(self):
        properties = _get_network_properties()
        self.assertEqual(properties[0].key, "rp")
        self.assertEqual(properties[1].key, "attach")
        self.assertEqual(properties[2].key, "cikey")
        self.assertEqual(properties[3].key, "runtimeVersion")
        self.assertEqual(properties[4].key, "os")
        self.assertEqual(properties[5].key, "language")
        self.assertEqual(properties[6].key, "version")

    def test_get_common_properties(self):
        properties = _get_common_properties()
        self.assertEqual(properties[0].key, "rp")
        self.assertEqual(properties[1].key, "attach")
        self.assertEqual(properties[2].key, "cikey")
        self.assertEqual(properties[3].key, "runtimeVersion")
        self.assertEqual(properties[4].key, "os")
        self.assertEqual(properties[5].key, "language")
        self.assertEqual(properties[6].key, "version")

    def test_get_success_count_value(self):
        _requests_map.clear()
        _requests_map['success'] = 10
        self.assertEqual(_get_success_count_value(), 10)
        self.assertEqual(_requests_map['success'], 0)
        _requests_map.clear()

    def test_get_failure_count_value(self):
        _requests_map.clear()
        _requests_map['failure'] = {}
        _requests_map['failure'][400] = 10
        self.assertEqual(_get_failure_count_value(400), 10)
        self.assertEqual(_requests_map['failure'][400], 0)
        _requests_map.clear()

    def test_get_average_duration_value(self):
        _requests_map.clear()
        _requests_map['duration'] = 10
        _requests_map['count'] = 2
        self.assertEqual(_get_average_duration_value(), 5000.0)
        self.assertEqual(_requests_map['duration'], 0)
        self.assertEqual(_requests_map['count'], 0)
        _requests_map.clear()

    def test_get_retry_count_value(self):
        _requests_map.clear()
        _requests_map['retry'] = {}
        _requests_map['retry'][401] = 10
        self.assertEqual(_get_retry_count_value(401), 10)
        self.assertEqual(_requests_map['retry'][401], 0)
        _requests_map.clear()

    def test_get_throttle_count_value(self):
        _requests_map.clear()
        _requests_map['throttle'] = {}
        _requests_map['throttle'][402] = 10
        self.assertEqual(_get_throttle_count_value(402), 10)
        self.assertEqual(_requests_map['throttle'][402], 0)
        _requests_map.clear()

    def test_get_exception_count_value(self):
        _requests_map.clear()
        _requests_map['exception'] = {}
        _requests_map['exception']['Timeout'] = 10
        self.assertEqual(_get_exception_count_value('Timeout'), 10)
        self.assertEqual(_requests_map['exception']['Timeout'], 0)
        _requests_map.clear()

    def test_statsbeat_metric_get_initial_metrics(self):
        # pylint: disable=protected-access
        metric = _StatsbeatMetrics(_OPTIONS)
        attach_metric_mock = mock.Mock()
        attach_metric_mock.return_value = "attach"
        feature_metric_mock = mock.Mock()
        feature_metric_mock.return_value = "feature"
        instr_metric_mock = mock.Mock()
        instr_metric_mock.return_value = "instr"
        metric._get_attach_metric = attach_metric_mock
        metric._get_feature_metric = feature_metric_mock
        metric._get_instrumentation_metric = instr_metric_mock
        metrics = metric.get_initial_metrics()
        attach_metric_mock.assert_called_once()
        feature_metric_mock.assert_called_once()
        instr_metric_mock.assert_called_once()
        self.assertEqual(metrics, ["attach", "feature", "instr"])

    def test_statsbeat_metric_get_metrics(self):
        # pylint: disable=protected-access
        metric = _StatsbeatMetrics(_OPTIONS)
        metric._long_threshold_count = _STATS_LONG_INTERVAL_THRESHOLD
        initial_metric_mock = mock.Mock()
        network_metric_mock = mock.Mock()
        initial_metric_mock.return_value = ["initial"]
        network_metric_mock.return_value = ["network"]
        metric.get_initial_metrics = initial_metric_mock
        metric._get_network_metrics = network_metric_mock
        metrics = metric.get_metrics()
        initial_metric_mock.assert_called_once()
        network_metric_mock.assert_called_once()
        self.assertEqual(metrics, ["initial", "network"])
        self.assertEqual(metric._long_threshold_count, 0)

    def test_statsbeat_metric_get_metrics_short(self):
        # pylint: disable=protected-access
        metric = _StatsbeatMetrics(_OPTIONS)
        metric._long_threshold_count = 1
        initial_metric_mock = mock.Mock()
        network_metric_mock = mock.Mock()
        initial_metric_mock.return_value = ["initial"]
        network_metric_mock.return_value = ["network"]
        metric.get_initial_metrics = initial_metric_mock
        metric._get_network_metrics = network_metric_mock
        metrics = metric.get_metrics()
        initial_metric_mock.assert_not_called()
        network_metric_mock.assert_called_once()
        self.assertEqual(metrics, ["network"])
        self.assertEqual(metric._long_threshold_count, 2)

    def test_get_feature_metric(self):
        stats = _StatsbeatMetrics(_OPTIONS)
        metric = stats._get_feature_metric()
        properties = metric._time_series[0]._label_values
        self.assertEqual(len(properties), 9)
        self.assertEqual(properties[0].value, _RP_NAMES[3])
        self.assertEqual(properties[1].value, "sdk")
        self.assertEqual(properties[2].value, "ikey")
        self.assertEqual(properties[3].value, platform.python_version())
        self.assertEqual(properties[4].value, _FEATURE_TYPES.FEATURE)
        self.assertEqual(properties[5].value, 1)
        self.assertEqual(properties[6].value, platform.system())
        self.assertEqual(properties[7].value, "python")
        self.assertEqual(
            properties[8].value, ext_version)  # noqa: E501

    def test_get_feature_metric_with_aad(self):
        aad_options = Options(
            instrumentation_key="ikey",
            enable_local_storage=True,
            endpoint="test-endpoint",
            credential=MockCredential(),
        )
        stats = _StatsbeatMetrics(aad_options)
        metric = stats._get_feature_metric()
        properties = metric._time_series[0]._label_values
        self.assertEqual(len(properties), 9)
        self.assertEqual(properties[0].value, _RP_NAMES[3])
        self.assertEqual(properties[1].value, "sdk")
        self.assertEqual(properties[2].value, "ikey")
        self.assertEqual(properties[3].value, platform.python_version())
        self.assertEqual(properties[4].value, _FEATURE_TYPES.FEATURE)
        self.assertEqual(properties[5].value, 3)
        self.assertEqual(properties[6].value, platform.system())
        self.assertEqual(properties[7].value, "python")
        self.assertEqual(
            properties[8].value, ext_version)  # noqa: E501

    def test_get_feature_metric_zero(self):
        # pylint: disable=protected-access
        options = Options(
            instrumentation_key="ikey",
            enable_local_storage=False,
            credential=None,
        )
        stats = _StatsbeatMetrics(options)
        metric = stats._get_feature_metric()
        self.assertIsNone(metric)

    def test_get_instrumentation_metric(self):
        original_integrations = integrations._INTEGRATIONS_BIT_MASK
        integrations._INTEGRATIONS_BIT_MASK = 1024
        stats = _StatsbeatMetrics(_OPTIONS)
        metric = stats._get_instrumentation_metric()
        properties = metric._time_series[0]._label_values
        self.assertEqual(len(properties), 9)
        self.assertEqual(properties[0].value, _RP_NAMES[3])
        self.assertEqual(properties[1].value, "sdk")
        self.assertEqual(properties[2].value, "ikey")
        self.assertEqual(properties[3].value, platform.python_version())
        self.assertEqual(properties[4].value, _FEATURE_TYPES.INSTRUMENTATION)
        self.assertEqual(properties[5].value, 1024)
        self.assertEqual(properties[6].value, platform.system())
        self.assertEqual(properties[7].value, "python")
        self.assertEqual(
            properties[8].value, ext_version)  # noqa: E501
        integrations._INTEGRATIONS_BIT_MASK = original_integrations

    def test_get_instrumentation_metrics_zero(self):
        # pylint: disable=protected-access
        original_integrations = integrations._INTEGRATIONS_BIT_MASK
        integrations._INTEGRATIONS_BIT_MASK = 0
        stats = _StatsbeatMetrics(_OPTIONS)
        metric = stats._get_instrumentation_metric()
        self.assertIsNone(metric)
        integrations._INTEGRATIONS_BIT_MASK = original_integrations

    @mock.patch(
        'opencensus.ext.azure.statsbeat.statsbeat_metrics._get_exception_count_value')  # noqa: E501
    @mock.patch(
        'opencensus.ext.azure.statsbeat.statsbeat_metrics._get_throttle_count_value')  # noqa: E501
    @mock.patch(
        'opencensus.ext.azure.statsbeat.statsbeat_metrics._get_retry_count_value')  # noqa: E501
    @mock.patch(
        'opencensus.ext.azure.statsbeat.statsbeat_metrics._get_average_duration_value')  # noqa: E501
    @mock.patch(
        'opencensus.ext.azure.statsbeat.statsbeat_metrics._get_failure_count_value')  # noqa: E501
    @mock.patch(
        'opencensus.ext.azure.statsbeat.statsbeat_metrics._get_success_count_value')  # noqa: E501
    def test_get_network_metrics(self, mock1, mock2, mock3, mock4, mock5, mock6):  # noqa: E501
        # pylint: disable=protected-access
        _requests_map.clear()
        _requests_map['exception'] = {}
        _requests_map['throttle'] = {}
        _requests_map['retry'] = {}
        _requests_map['failure'] = {}
        _requests_map['exception']['Timeout'] = 5
        _requests_map['exception']['RequestException'] = 5
        _requests_map['throttle'][402] = 5
        _requests_map['throttle'][439] = 5
        _requests_map['retry'][401] = 5
        _requests_map['retry'][403] = 5
        _requests_map['failure'][400] = 5
        _requests_map['failure'][404] = 5
        stats = _StatsbeatMetrics(_OPTIONS)
        mock1.return_value = 5
        mock2.return_value = 5
        mock3.return_value = 5
        mock4.return_value = 5
        mock5.return_value = 5
        mock6.return_value = 5
        metrics = stats._get_network_metrics()
        mock1.assert_called_once()
        self.assertEqual(mock2.call_count, 2)
        mock3.assert_called_once()
        self.assertEqual(mock4.call_count, 2)
        self.assertEqual(mock5.call_count, 2)
        self.assertEqual(mock6.call_count, 2)
        self.assertEqual(len(metrics), 6)
        for metric in metrics:
            for ts in metric._time_series:
                properties = ts._label_values
                if metric.descriptor.name == _REQ_DURATION_NAME:
                    self.assertEqual(len(properties), 9)
                else:
                    self.assertEqual(len(properties), 10)
                if metric.descriptor.name == _REQ_SUCCESS_NAME:
                    self.assertEqual(ts.points[0].value.value, 5)
                    self.assertEqual(properties[9].value, 200)
                if metric.descriptor.name == _REQ_DURATION_NAME:
                    self.assertEqual(ts.points[0].value.value, 5)
                if metric.descriptor.name == _REQ_FAILURE_NAME:
                    self.assertEqual(ts.points[0].value.value, 5)
                    self.assertTrue(properties[9].value in (400, 404))
                if metric.descriptor.name == _REQ_RETRY_NAME:
                    self.assertEqual(ts.points[0].value.value, 5)
                    self.assertTrue(properties[9].value in (401, 403))
                if metric.descriptor.name == _REQ_THROTTLE_NAME:
                    self.assertEqual(ts.points[0].value.value, 5)
                    self.assertTrue(properties[9].value in (402, 439))
                if metric.descriptor.name == _REQ_EXCEPTION_NAME:
                    self.assertEqual(ts.points[0].value.value, 5)
                    self.assertTrue(properties[9].value in ('Timeout', 'RequestException'))  # noqa: E501
                self.assertEqual(properties[0].value, _RP_NAMES[3])
                self.assertEqual(properties[1].value, "sdk")
                self.assertEqual(properties[2].value, "ikey")
                self.assertEqual(properties[3].value, platform.python_version())  # noqa: E501
                self.assertEqual(properties[4].value, platform.system())
                self.assertEqual(properties[5].value, "python")
                self.assertEqual(properties[6].value, ext_version)
                self.assertEqual(properties[7].value, _ENDPOINT_TYPES[0])
                short_host = _shorten_host(_OPTIONS.endpoint)
                self.assertEqual(properties[8].value, short_host)
        _requests_map.clear()

    @mock.patch(
        'opencensus.ext.azure.statsbeat.statsbeat_metrics._get_success_count_value')  # noqa: E501
    @mock.patch(
        'opencensus.ext.azure.statsbeat.statsbeat_metrics._get_average_duration_value')  # noqa: E501
    def test_get_network_metrics_zero(self, suc_mock, dur_mock):
        # pylint: disable=protected-access
        _requests_map.clear()
        stats = _StatsbeatMetrics(_OPTIONS)
        suc_mock.return_value = 0
        dur_mock.return_value = 0
        metrics = stats._get_network_metrics()
        self.assertEqual(len(metrics), 2)
        self.assertEqual(metrics[0]._time_series[0].points[0].value.value, 0)
        self.assertEqual(metrics[1]._time_series[0].points[0].value.value, 0)

    @mock.patch.dict(
        os.environ,
        {
            "WEBSITE_SITE_NAME": "site_name",
            "WEBSITE_HOME_STAMPNAME": "stamp_name",
        }
    )
    def test_get_attach_metric_appsvc(self):
        # pylint: disable=protected-access
        stats = _StatsbeatMetrics(_OPTIONS)
        metric = stats._get_attach_metric()
        properties = metric._time_series[0]._label_values
        self.assertEqual(len(properties), 8)
        self.assertEqual(properties[0].value, _RP_NAMES[0])
        self.assertEqual(properties[1].value, "site_name/stamp_name")
        self.assertEqual(properties[2].value, "sdk")
        self.assertEqual(properties[3].value, "ikey")
        self.assertEqual(properties[4].value, platform.python_version())
        self.assertEqual(properties[5].value, platform.system())
        self.assertEqual(properties[6].value, "python")
        self.assertEqual(
            properties[7].value, ext_version)  # noqa: E501

    @mock.patch.dict(
        os.environ,
        {
            "FUNCTIONS_WORKER_RUNTIME": "runtime",
            "WEBSITE_HOSTNAME": "host_name",
            "WEBSITE_SITE_NAME": "site_name",
        }
    )
    def test_get_attach_metric_functions(self):
        # pylint: disable=protected-access
        stats = _StatsbeatMetrics(_OPTIONS)
        metric = stats._get_attach_metric()
        properties = metric._time_series[0]._label_values
        self.assertEqual(len(properties), 8)
        self.assertEqual(properties[0].value, _RP_NAMES[1])
        self.assertEqual(properties[1].value, "host_name")
        self.assertEqual(properties[2].value, "sdk")
        self.assertEqual(properties[3].value, "ikey")
        self.assertEqual(properties[4].value, platform.python_version())
        self.assertEqual(properties[5].value, platform.system())
        self.assertEqual(properties[6].value, "python")
        self.assertEqual(
            properties[7].value, ext_version)  # noqa: E501

    def test_get_attach_metric_vm(self):
        stats = _StatsbeatMetrics(_OPTIONS)
        _vm_data = {}
        _vm_data["vmId"] = "123"
        _vm_data["subscriptionId"] = "sub123"
        _vm_data["osType"] = "linux"
        stats._vm_data = _vm_data
        stats._vm_retry = True
        metadata_mock = mock.Mock()
        metadata_mock.return_value = True
        stats._get_azure_compute_metadata = metadata_mock
        metric = stats._get_attach_metric()
        properties = metric._time_series[0]._label_values
        self.assertEqual(len(properties), 8)
        self.assertEqual(properties[0].value, _RP_NAMES[2])
        self.assertEqual(properties[1].value, "123/sub123")
        self.assertEqual(properties[2].value, "sdk")
        self.assertEqual(properties[3].value, "ikey")
        self.assertEqual(properties[4].value, platform.python_version())
        self.assertEqual(properties[5].value, "linux")
        self.assertEqual(properties[6].value, "python")
        self.assertEqual(
            properties[7].value, ext_version)  # noqa: E501

    def test_get_attach_metric_vm_no_os(self):
        stats = _StatsbeatMetrics(_OPTIONS)
        _vm_data = {}
        _vm_data["vmId"] = "123"
        _vm_data["subscriptionId"] = "sub123"
        _vm_data["osType"] = None
        stats._vm_data = _vm_data
        stats._vm_retry = True
        metadata_mock = mock.Mock()
        metadata_mock.return_value = True
        stats._get_azure_compute_metadata = metadata_mock
        metric = stats._get_attach_metric()
        properties = metric._time_series[0]._label_values
        self.assertEqual(len(properties), 8)
        self.assertEqual(properties[5].value, platform.system())

    def test_get_attach_metric_unknown(self):
        stats = _StatsbeatMetrics(_OPTIONS)
        stats._vm_retry = False
        metric = stats._get_attach_metric()
        properties = metric._time_series[0]._label_values
        self.assertEqual(len(properties), 8)
        self.assertEqual(properties[0].value, _RP_NAMES[3])
        self.assertEqual(properties[1].value, _RP_NAMES[3])
        self.assertEqual(properties[2].value, "sdk")
        self.assertEqual(properties[3].value, "ikey")
        self.assertEqual(properties[4].value, platform.python_version())
        self.assertEqual(properties[5].value, platform.system())
        self.assertEqual(properties[6].value, "python")
        self.assertEqual(
            properties[7].value, ext_version)  # noqa: E501

    def test_get_azure_compute_metadata(self):
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
            stats = _StatsbeatMetrics(_OPTIONS)
            vm_result = stats._get_azure_compute_metadata()
            self.assertTrue(vm_result)
            self.assertEqual(stats._vm_data["vmId"], 5)
            self.assertEqual(stats._vm_data["subscriptionId"], 3)
            self.assertEqual(stats._vm_data["osType"], "Linux")
            self.assertTrue(stats._vm_retry)

    def test_get_azure_compute_metadata_not_vm(self):
        with mock.patch(
            'requests.get',
            throw(requests.exceptions.ConnectionError)
        ):
            stats = _StatsbeatMetrics(_OPTIONS)
            vm_result = stats._get_azure_compute_metadata()
            self.assertFalse(vm_result)
            self.assertEqual(len(stats._vm_data), 0)
            self.assertFalse(stats._vm_retry)

    def test_get_azure_compute_metadata_not_vm_timeout(self):
        with mock.patch(
            'requests.get',
            throw(requests.Timeout)
        ):
            stats = _StatsbeatMetrics(_OPTIONS)
            vm_result = stats._get_azure_compute_metadata()
            self.assertFalse(vm_result)
            self.assertEqual(len(stats._vm_data), 0)
            self.assertFalse(stats._vm_retry)

    def test_get_azure_compute_metadata_vm_retry(self):
        with mock.patch(
            'requests.get',
            throw(requests.exceptions.RequestException)
        ):
            stats = _StatsbeatMetrics(_OPTIONS)
            vm_result = stats._get_azure_compute_metadata()
            self.assertFalse(vm_result)
            self.assertEqual(len(stats._vm_data), 0)
            self.assertTrue(stats._vm_retry)

    def test_shorten_host(self):
        url = "https://fakehost-1.example.com/"
        self.assertEqual(_shorten_host(url), "fakehost-1")
        url = "https://fakehost-2.example.com/"
        self.assertEqual(_shorten_host(url), "fakehost-2")
        url = "http://www.fakehost-3.example.com/"
        self.assertEqual(_shorten_host(url), "fakehost-3")
        url = "http://www.fakehost.com/v2/track"
        self.assertEqual(_shorten_host(url), "fakehost")
        url = "https://www.fakehost0-4.com/"
        self.assertEqual(_shorten_host(url), "fakehost0-4")
        url = "https://www.fakehost-5.com"
        self.assertEqual(_shorten_host(url), "fakehost-5")
        url = "https://fakehost.com"
        self.assertEqual(_shorten_host(url), "fakehost")
        url = "http://fakehost-5/"
        self.assertEqual(_shorten_host(url), "fakehost-5")

    def test_get_stats_connection_string_env(self):
        cs = "InstrumentationKey=1aa11111-bbbb-1ccc-8ddd-eeeeffff3333;IngestionEndpoint=https://westus-0.in.applicationinsights.azure.com/"  # noqa: E501
        with mock.patch.dict(
            os.environ, {
                "APPLICATION_INSIGHTS_STATS_CONNECTION_STRING": cs
            }
        ):
            stats_cs = _get_stats_connection_string(_OPTIONS.endpoint)
            self.assertEqual(stats_cs, cs)

    def test_get_stats_connection_string_non_eu(self):
        with mock.patch.dict(
            os.environ, {
                "APPLICATION_INSIGHTS_STATS_CONNECTION_STRING": ""
            }
        ):
            cs = "InstrumentationKey=1aa11111-bbbb-1ccc-8ddd-eeeeffff3333;IngestionEndpoint=https://westus-0.in.applicationinsights.azure.com/"  # noqa: E501
            non_eu = Options(
                connection_string=cs,
            )
            stats_cs = _get_stats_connection_string(non_eu.endpoint)
            self.assertEqual(stats_cs, _DEFAULT_NON_EU_STATS_CONNECTION_STRING)

    def test_get_stats_connection_string_eu(self):
        with mock.patch.dict(
            os.environ, {
                "APPLICATION_INSIGHTS_STATS_CONNECTION_STRING": ""
            }
        ):
            cs = "InstrumentationKey=1aa11111-bbbb-1ccc-8ddd-eeeeffff3333;IngestionEndpoint=https://northeurope-0.in.applicationinsights.azure.com/"  # noqa: E501
            eu = Options(
                connection_string=cs,
            )
            stats_cs = _get_stats_connection_string(eu.endpoint)
            self.assertEqual(stats_cs, _DEFAULT_EU_STATS_CONNECTION_STRING)
