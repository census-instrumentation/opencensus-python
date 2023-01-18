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

import datetime
import json
import os
import platform
import re
import threading

import requests

from opencensus.ext.azure.common.transport import _requests_lock, _requests_map
from opencensus.ext.azure.common.version import __version__ as ext_version
from opencensus.metrics.export.gauge import (
    DerivedDoubleGauge,
    DerivedLongGauge,
    LongGauge,
)
from opencensus.metrics.label_key import LabelKey
from opencensus.metrics.label_value import LabelValue
from opencensus.trace.integrations import _Integrations, get_integrations

_AIMS_URI = "http://169.254.169.254/metadata/instance/compute"
_AIMS_API_VERSION = "api-version=2017-12-01"
_AIMS_FORMAT = "format=json"

_DEFAULT_NON_EU_STATS_CONNECTION_STRING = "InstrumentationKey=c4a29126-a7cb-47e5-b348-11414998b11e;IngestionEndpoint=https://westus-0.in.applicationinsights.azure.com/"  # noqa: E501
_DEFAULT_EU_STATS_CONNECTION_STRING = "InstrumentationKey=7dc56bab-3c0c-4e9f-9ebb-d1acadee8d0f;IngestionEndpoint=https://westeurope-5.in.applicationinsights.azure.com/"  # noqa: E501
_DEFAULT_STATS_SHORT_EXPORT_INTERVAL = 900  # 15 minutes
_DEFAULT_STATS_LONG_EXPORT_INTERVAL = 86400  # 24 hours
_EU_ENDPOINTS = [
    "westeurope",
    "northeurope",
    "francecentral",
    "francesouth",
    "germanywestcentral",
    "norwayeast",
    "norwaywest",
    "swedencentral",
    "switzerlandnorth",
    "switzerlandwest",
    "uksouth",
    "ukwest",
]

_ATTACH_METRIC_NAME = "Attach"
_FEATURE_METRIC_NAME = "Feature"
_REQ_SUCCESS_NAME = "Request Success Count"
_REQ_FAILURE_NAME = "Request Failure Count"
_REQ_DURATION_NAME = "Request Duration"
_REQ_RETRY_NAME = "Retry Count"
_REQ_THROTTLE_NAME = "Throttle Count"
_REQ_EXCEPTION_NAME = "Exception Count"

_NETWORK_STATSBEAT_NAMES = (
    _REQ_SUCCESS_NAME,
    _REQ_FAILURE_NAME,
    _REQ_DURATION_NAME,
    _REQ_RETRY_NAME,
    _REQ_THROTTLE_NAME,
    _REQ_EXCEPTION_NAME,
)

_ENDPOINT_TYPES = ["breeze"]
_RP_NAMES = ["appsvc", "functions", "vm", "unknown"]

_HOST_PATTERN = re.compile('^https?://(?:www\\.)?([^/.]+)')


class _FEATURE_TYPES:
    FEATURE = 0
    INSTRUMENTATION = 1


class _StatsbeatFeature:
    NONE = 0
    DISK_RETRY = 1
    AAD = 2


def _get_stats_connection_string(endpoint):
    cs_env = os.environ.get("APPLICATION_INSIGHTS_STATS_CONNECTION_STRING")
    if cs_env:
        return cs_env
    else:
        for ep in _EU_ENDPOINTS:
            if ep in endpoint:
                # Use statsbeat EU endpoint if user is in EU region
                return _DEFAULT_EU_STATS_CONNECTION_STRING
        return _DEFAULT_NON_EU_STATS_CONNECTION_STRING


def _get_stats_short_export_interval():
    ei_env = os.environ.get("APPLICATION_INSIGHTS_STATS_SHORT_EXPORT_INTERVAL")
    if ei_env:
        return int(ei_env)
    else:
        return _DEFAULT_STATS_SHORT_EXPORT_INTERVAL


def _get_stats_long_export_interval():
    ei_env = os.environ.get("APPLICATION_INSIGHTS_STATS_LONG_EXPORT_INTERVAL")
    if ei_env:
        return int(ei_env)
    else:
        return _DEFAULT_STATS_LONG_EXPORT_INTERVAL


_STATS_SHORT_EXPORT_INTERVAL = _get_stats_short_export_interval()
_STATS_LONG_EXPORT_INTERVAL = _get_stats_long_export_interval()
_STATS_LONG_INTERVAL_THRESHOLD = _STATS_LONG_EXPORT_INTERVAL / _STATS_SHORT_EXPORT_INTERVAL  # noqa: E501


def _get_common_properties():
    properties = []
    properties.append(
        LabelKey("rp", 'name of the rp, e.g. appsvc, vm, function, aks, etc.'))
    properties.append(LabelKey("attach", 'codeless or sdk'))
    properties.append(LabelKey("cikey", 'customer ikey'))
    properties.append(LabelKey("runtimeVersion", 'Python version'))
    properties.append(LabelKey("os", 'os of application being instrumented'))
    properties.append(LabelKey("language", 'Python'))
    properties.append(LabelKey("version", 'sdkVersion - version of the ext'))
    return properties


def _get_attach_properties():
    properties = _get_common_properties()
    properties.insert(1, LabelKey("rpId", 'unique id of rp'))
    return properties


def _get_network_properties(value=None):
    properties = _get_common_properties()
    properties.append(LabelKey("endpoint", "ingestion endpoint type"))
    properties.append(LabelKey("host", "destination of ingestion endpoint"))
    if value is None:
        properties.append(LabelKey("statusCode", "ingestion service response code"))  # noqa: E501
    elif value == "Exception":
        properties.append(LabelKey("exceptionType", "language specific exception type"))  # noqa: E501
    return properties


def _get_feature_properties():
    properties = _get_common_properties()
    properties.insert(4, LabelKey("feature", 'represents enabled features'))
    properties.insert(4, LabelKey("type", 'type, either feature or instrumentation'))  # noqa: E501
    return properties


def _get_success_count_value():
    with _requests_lock:
        interval_count = _requests_map.get('success', 0)
        _requests_map['success'] = 0
        return interval_count


def _get_failure_count_value(status_code):
    interval_count = 0
    if status_code:
        with _requests_lock:
            if _requests_map.get('failure'):
                interval_count = _requests_map.get('failure').get(status_code, 0)  # noqa: E501
                _requests_map['failure'][status_code] = 0
    return interval_count


def _get_average_duration_value():
    with _requests_lock:
        interval_duration = _requests_map.get('duration', 0)
        interval_count = _requests_map.get('count', 0)
        _requests_map['duration'] = 0
        _requests_map['count'] = 0
        if interval_duration > 0 and interval_count > 0:
            result = interval_duration / interval_count
            # Convert to milliseconds
            return result * 1000.0
        return 0


def _get_retry_count_value(status_code):
    interval_count = 0
    if status_code:
        with _requests_lock:
            if _requests_map.get('retry'):
                interval_count = _requests_map.get('retry').get(status_code, 0)
                _requests_map['retry'][status_code] = 0
    return interval_count


def _get_throttle_count_value(status_code):
    interval_count = 0
    if status_code:
        with _requests_lock:
            if _requests_map.get('throttle'):
                interval_count = _requests_map.get('throttle').get(status_code, 0)  # noqa: E501
                _requests_map['throttle'][status_code] = 0
    return interval_count


def _get_exception_count_value(exc_type):
    interval_count = 0
    if exc_type:
        with _requests_lock:
            if _requests_map.get('exception'):
                interval_count = _requests_map.get('exception').get(exc_type, 0)  # noqa: E501
                _requests_map['exception'][exc_type] = 0
    return interval_count


def _shorten_host(host):
    if not host:
        host = ""
    match = _HOST_PATTERN.match(host)
    if match:
        host = match.group(1)
    return host


class _StatsbeatMetrics:

    def __init__(self, options):
        self._options = options
        self._instrumentation_key = options.instrumentation_key
        self._feature = _StatsbeatFeature.NONE
        if options.enable_local_storage:
            self._feature |= _StatsbeatFeature.DISK_RETRY
        if options.credential:
            self._feature |= _StatsbeatFeature.AAD
        self._stats_lock = threading.Lock()
        self._vm_data = {}
        self._vm_retry = True
        self._rp = _RP_NAMES[3]
        self._os_type = platform.system()
        # Attach metrics - metrics related to rp (resource provider)
        self._attach_metric = LongGauge(
            _ATTACH_METRIC_NAME,
            'Statsbeat metric related to rp integrations',
            'count',
            _get_attach_properties(),
        )
        # Keep track of how many iterations until long export
        self._long_threshold_count = 0
        # Network metrics - metrics related to request calls to Breeze
        self._network_metrics = {}
        # Map of gauge function -> metric
        # Gauge function is the callback used to populate the metric value
        self._network_metrics[_get_success_count_value] = DerivedLongGauge(
            _REQ_SUCCESS_NAME,
            'Statsbeat metric tracking request success count',
            'count',
            _get_network_properties(),
        )
        self._network_metrics[_get_failure_count_value] = DerivedLongGauge(
            _REQ_FAILURE_NAME,
            'Statsbeat metric tracking request failure count',
            'count',
            _get_network_properties(),
        )
        self._network_metrics[_get_average_duration_value] = DerivedDoubleGauge(  # noqa: E501
            _REQ_DURATION_NAME,
            'Statsbeat metric tracking average request duration',
            'avg',
            _get_network_properties(value="Duration"),
        )
        self._network_metrics[_get_retry_count_value] = DerivedLongGauge(
            _REQ_RETRY_NAME,
            'Statsbeat metric tracking request retry count',
            'count',
            _get_network_properties(),
        )
        self._network_metrics[_get_throttle_count_value] = DerivedLongGauge(
            _REQ_THROTTLE_NAME,
            'Statsbeat metric tracking request throttle count',
            'count',
            _get_network_properties(),
        )
        self._network_metrics[_get_exception_count_value] = DerivedLongGauge(
            _REQ_EXCEPTION_NAME,
            'Statsbeat metric tracking request exception count',
            'count',
            _get_network_properties(value="Exception"),
        )
        # feature/instrumentation metrics
        # metrics related to what features and instrumentations are enabled
        self._feature_metric = LongGauge(
            _FEATURE_METRIC_NAME,
            'Statsbeat metric related to features enabled',  # noqa: E501
            'count',
            _get_feature_properties(),
        )
        # Instrumentation metric uses same name/properties as feature
        self._instrumentation_metric = LongGauge(
            _FEATURE_METRIC_NAME,
            'Statsbeat metric related to instrumentations enabled',  # noqa: E501
            'count',
            _get_feature_properties(),
        )

    # Metrics that are sent on application start
    def get_initial_metrics(self):
        stats_metrics = []
        if self._attach_metric:
            attach_metric = self._get_attach_metric()
            if attach_metric:
                stats_metrics.append(attach_metric)
        if self._feature_metric:
            feature_metric = self._get_feature_metric()
            if feature_metric:
                stats_metrics.append(feature_metric)
        if self._instrumentation_metric:
            instr_metric = self._get_instrumentation_metric()
            if instr_metric:
                stats_metrics.append(instr_metric)
        return stats_metrics

    # Metrics sent every statsbeat interval
    def get_metrics(self):
        metrics = []
        try:
            # Initial metrics use the long export interval
            # Only export once long count hits threshold
            with self._stats_lock:
                self._long_threshold_count = self._long_threshold_count + 1
                if self._long_threshold_count >= _STATS_LONG_INTERVAL_THRESHOLD:  # noqa: E501
                    metrics.extend(self.get_initial_metrics())
                    self._long_threshold_count = 0
            network_metrics = self._get_network_metrics()
            metrics.extend(network_metrics)
        except Exception:
            pass

        return metrics

    def _get_network_metrics(self):
        properties = self._get_common_properties()
        properties.append(LabelValue(_ENDPOINT_TYPES[0]))  # endpoint
        host = _shorten_host(self._options.endpoint)
        properties.append(LabelValue(host))  # host
        metrics = []
        for fn, metric in self._network_metrics.items():
            if metric.descriptor.name == _REQ_SUCCESS_NAME:
                properties.append(LabelValue(200))
                metric.create_time_series(properties, fn)
                properties.pop()
            elif metric.descriptor.name == _REQ_FAILURE_NAME:
                for code in _requests_map.get('failure', {}).keys():
                    properties.append(LabelValue(code))
                    metric.create_time_series(properties, fn, status_code=code)
                    properties.pop()
            elif metric.descriptor.name == _REQ_DURATION_NAME:
                metric.create_time_series(properties, fn)
            elif metric.descriptor.name == _REQ_RETRY_NAME:
                for code in _requests_map.get('retry', {}).keys():
                    properties.append(LabelValue(code))
                    metric.create_time_series(properties, fn, status_code=code)
                    properties.pop()
            elif metric.descriptor.name == _REQ_THROTTLE_NAME:
                for code in _requests_map.get('throttle', {}).keys():
                    properties.append(LabelValue(code))
                    metric.create_time_series(properties, fn, status_code=code)
                    properties.pop()
            elif metric.descriptor.name == _REQ_EXCEPTION_NAME:
                for exc_type in _requests_map.get('exception', {}).keys():
                    properties.append(LabelValue(exc_type))
                    metric.create_time_series(properties, fn, exc_type=exc_type)  # noqa: E501
                    properties.pop()

            stats_metric = metric.get_metric(datetime.datetime.utcnow())
            # metric will be None if status_code or exc_type is invalid
            # for success count, this will never be None
            if stats_metric is not None:
                # we handle not exporting of None and 0 values in the exporter
                metrics.append(stats_metric)
        return metrics

    def _get_feature_metric(self):
        # Don't export if feature list is None
        if self._feature is _StatsbeatFeature.NONE:
            return None
        properties = self._get_common_properties()
        properties.insert(4, LabelValue(self._feature))  # feature long
        properties.insert(4, LabelValue(_FEATURE_TYPES.FEATURE))  # type
        self._feature_metric.get_or_create_time_series(properties)
        return self._feature_metric.get_metric(datetime.datetime.utcnow())

    def _get_instrumentation_metric(self):
        integrations = get_integrations()
        # Don't export if instrumentation list is None
        if integrations is _Integrations.NONE:
            return None
        properties = self._get_common_properties()
        properties.insert(4, LabelValue(get_integrations()))  # instr long
        properties.insert(4, LabelValue(_FEATURE_TYPES.INSTRUMENTATION))  # type  # noqa: E501
        self._instrumentation_metric.get_or_create_time_series(properties)
        return self._instrumentation_metric.get_metric(datetime.datetime.utcnow())  # noqa: E501

    def _get_attach_metric(self):
        properties = []
        rp = ''
        rpId = ''
        # rp, rpId
        if os.environ.get("WEBSITE_SITE_NAME") is not None:
            # Web apps
            rp = _RP_NAMES[0]
            rpId = '{}/{}'.format(
                        os.environ.get("WEBSITE_SITE_NAME"),
                        os.environ.get("WEBSITE_HOME_STAMPNAME", '')
            )
        elif os.environ.get("FUNCTIONS_WORKER_RUNTIME") is not None:
            # Function apps
            rp = _RP_NAMES[1]
            rpId = os.environ.get("WEBSITE_HOSTNAME")
        elif self._vm_retry and self._get_azure_compute_metadata():
            # VM
            rp = _RP_NAMES[2]
            rpId = '{}/{}'.format(
                        self._vm_data.get("vmId", ''),
                        self._vm_data.get("subscriptionId", ''))
            self._os_type = self._vm_data.get("osType", '')
        else:
            # Not in any rp or VM metadata failed
            rp = _RP_NAMES[3]
            rpId = _RP_NAMES[3]

        self._rp = rp
        properties.extend(self._get_common_properties())
        properties.insert(1, LabelValue(rpId))  # rpid
        self._attach_metric.get_or_create_time_series(properties)
        return self._attach_metric.get_metric(datetime.datetime.utcnow())

    def _get_common_properties(self):
        properties = []
        properties.append(LabelValue(self._rp))  # rp
        properties.append(LabelValue("sdk"))  # attach type
        properties.append(LabelValue(self._instrumentation_key))  # cikey
        # runTimeVersion
        properties.append(LabelValue(platform.python_version()))
        properties.append(LabelValue(self._os_type or platform.system()))  # os
        properties.append(LabelValue("python"))  # language
        properties.append(LabelValue(ext_version))  # version
        return properties

    def _get_azure_compute_metadata(self):
        try:
            request_url = "{0}?{1}&{2}".format(
                _AIMS_URI, _AIMS_API_VERSION, _AIMS_FORMAT)
            response = requests.get(
                request_url, headers={"MetaData": "True"}, timeout=5.0)
        except (requests.exceptions.ConnectionError, requests.Timeout):
            # Not in VM
            self._vm_retry = False
            return False
        except requests.exceptions.RequestException:
            self._vm_retry = True  # retry
            return False

        try:
            text = response.text
            self._vm_data = json.loads(text)
        except Exception:  # pylint: disable=broad-except
            # Error in reading response body, retry
            self._vm_retry = True
            return False

        # Vm data is perpetually updated
        self._vm_retry = True
        return True
