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

import requests

from opencensus.ext.azure.common.version import __version__ as ext_version
from opencensus.metrics.export.gauge import LongGauge
from opencensus.metrics.label_key import LabelKey
from opencensus.metrics.label_value import LabelValue

_AIMS_URI = "http://169.254.169.254/metadata/instance/compute"
_AIMS_API_VERSION = "api-version=2017-12-01"
_AIMS_FORMAT = "format=json"

_DEFAULT_STATS_CONNECTION_STRING = "InstrumentationKey=c4a29126-a7cb-47e5-b348-11414998b11e;IngestionEndpoint=https://dc.services.visualstudio.com/"  # noqa: E501
_DEFAULT_STATS_SHORT_EXPORT_INTERVAL = 900  # 15 minutes
_DEFAULT_STATS_LONG_EXPORT_INTERVAL = 86400  # 24 hours

_ATTACH_METRIC_NAME = "Attach"

_RP_NAMES = ["appsvc", "function", "vm", "unknown"]


def _get_stats_connection_string():
    cs_env = os.environ.get("APPLICATION_INSIGHTS_STATS_CONNECTION_STRING")
    if cs_env:
        return cs_env
    else:
        return _DEFAULT_STATS_CONNECTION_STRING


def _get_stats_short_export_interval():
    ei_env = os.environ.get("APPLICATION_INSIGHTS_STATS_SHORT_EXPORT_INTERVAL")
    if ei_env:
        return ei_env
    else:
        return _DEFAULT_STATS_SHORT_EXPORT_INTERVAL


def _get_stats_long_export_interval():
    ei_env = os.environ.get("APPLICATION_INSIGHTS_STATS_LONG_EXPORT_INTERVAL")
    if ei_env:
        return ei_env
    else:
        return _DEFAULT_STATS_LONG_EXPORT_INTERVAL


_STATS_CONNECTION_STRING = _get_stats_connection_string()
_STATS_SHORT_EXPORT_INTERVAL = _get_stats_short_export_interval()
_STATS_LONG_EXPORT_INTERVAL = _get_stats_long_export_interval()


def _get_attach_properties():
    properties = []
    properties.append(
        LabelKey("rp", 'name of the rp, e.g. appsvc, vm, function, aks, etc.'))
    properties.append(LabelKey("rpid", 'unique id of rp'))
    properties.append(LabelKey("attach", 'codeless or sdk'))
    properties.append(LabelKey("cikey", 'customer ikey'))
    properties.append(LabelKey("runtimeVersion", 'Python version'))
    properties.append(LabelKey("os", 'os of application being instrumented'))
    properties.append(LabelKey("language", 'Python'))
    properties.append(LabelKey("version", 'sdkVersion - version of the ext'))
    return properties


class _StatsbeatMetrics:

    def __init__(self, instrumentation_key):
        self._instrumentation_key = instrumentation_key
        self.vm_data = {}
        self.vm_retry = True
        # Attach metrics - metrics related to rp (resource provider)
        self._attach_metric = LongGauge(
            _ATTACH_METRIC_NAME,
            'Statsbeat metric related to rp integrations',
            'count',
            _get_attach_properties(),
        )

    def get_initial_metrics(self):
        stats_metrics = []
        if self._attach_metric:
            attach_metric = self._get_attach_metric(self._attach_metric)
            if attach_metric:
                stats_metrics.append(attach_metric)
        return stats_metrics

    def get_metrics(self):
        stats_metrics = self.get_initial_metrics()

        return stats_metrics

    def _get_attach_metric(self, metric):
        properties = []
        vm_os_type = ''
        # rpId
        if os.environ.get("WEBSITE_SITE_NAME") is not None:
            # Web apps
            properties.append(LabelValue(_RP_NAMES[0]))
            properties.append(
                LabelValue(
                    '{}/{}'.format(
                        os.environ.get("WEBSITE_SITE_NAME"),
                        os.environ.get("WEBSITE_HOME_STAMPNAME", '')),
                )
            )
        elif os.environ.get("FUNCTIONS_WORKER_RUNTIME") is not None:
            # Function apps
            properties.append(LabelValue(_RP_NAMES[1]))
            properties.append(LabelValue(os.environ.get("WEBSITE_HOSTNAME")))
        elif self.vm_retry and self._get_azure_compute_metadata():
            # VM
            properties.append(LabelValue(_RP_NAMES[2]))
            properties.append(
                LabelValue(
                    '{}//{}'.format(
                        self.vm_data.get("vmId", ''),
                        self.vm_data.get("subscriptionId", '')),
                )
            )
            vm_os_type = self.vm_data.get("osType", '')
        else:
            # Not in any rp or VM metadata failed
            properties.append(LabelValue(_RP_NAMES[3]))
            properties.append(LabelValue(_RP_NAMES[3]))

        properties.append(LabelValue("sdk"))  # attach type
        properties.append(LabelValue(self._instrumentation_key))  # cikey
        # runTimeVersion
        properties.append(LabelValue(platform.python_version()))
        properties.append(LabelValue(vm_os_type or platform.system()))  # os
        properties.append(LabelValue("python"))  # language
        # version
        properties.append(
            LabelValue(ext_version))
        metric.get_or_create_time_series(properties)
        return metric.get_metric(datetime.datetime.utcnow())

    def _get_azure_compute_metadata(self):
        try:
            request_url = "{0}?{1}&{2}".format(
                _AIMS_URI, _AIMS_API_VERSION, _AIMS_FORMAT)
            response = requests.get(
                request_url, headers={"MetaData": "True"}, timeout=5.0)
        except (requests.exceptions.ConnectionError, requests.Timeout):
            # Not in VM
            self.vm_retry = False
            return False
        except requests.exceptions.RequestException:
            self.vm_retry = True  # retry
            return False

        try:
            text = response.text
            self.vm_data = json.loads(text)
        except Exception:  # pylint: disable=broad-except
            # Error in reading response body, retry
            self.vm_retry = True
            return False

        # Vm data is perpetually updated
        self.vm_retry = True
        return True
