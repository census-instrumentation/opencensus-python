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
from collections import OrderedDict
from opencensus.ext.azure.metrics_exporter import statsbeat_metrics

import requests

from opencensus.ext.azure.common.utils import azure_monitor_context
from opencensus.metrics.export.gauge import LongGauge
from opencensus.metrics.label_key import LabelKey
from opencensus.metrics.label_value import LabelValue

_AIMS_URI = "http://169.254.169.254/metadata/instance/compute"
_AIMS_API_VERSION = "api-version=2017-12-01"
_AIMS_FORMAT = "format=json"

_TELEMETRY_NAME = "Statsbeat"
_ATTACH_METRIC_NAME = "Attach"

_RP_NAMES = ["aks","appsvc","function","vm"]


def _get_attach_properties():
    properties = []
    properties.append(LabelKey("rp", 'name of the rp, e.g. appsvc, vm, function, aks, etc.'))
    properties.append(LabelKey("rpid", 'unique id of rp'))
    properties.append(LabelKey("attach", 'codeless or sdk'))
    properties.append(LabelKey("cikey", 'customer ikey'))
    properties.append(LabelKey("runtimeVersion", 'Python version'))
    properties.append(LabelKey("os", 'os of application being instrumented'))
    properties.append(LabelKey("language", 'Python'))
    properties.append(LabelKey("version", 'version of exporter package'))
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

    def get_metrics(self):
        stats_metrics = []
        if self._attach_metric:
            attach_metric = self._get_attach_metric(self._attach_metric)
            if attach_metric:
                stats_metrics.append(attach_metric)

        return stats_metrics

    def _get_attach_metric(self, metric):
        properties = []
        os_type = ''
        # rpId
        if os.environ.get("WEBSITE_SITE_NAME") is not None:
            # Web apps
            properties.append(LabelValue(_RP_NAMES[1]))
            properties.append(
                LabelValue(
                    '{}/{}'.format(
                        os.environ.get("WEBSITE_SITE_NAME"),
                        os.environ.get("WEBSITE_HOME_STAMPNAME", '')),
                )
            )
        elif os.environ.get("FUNCTIONS_WORKER_RUNTIME") is not None:
            # Function apps
            properties.append(LabelValue(_RP_NAMES[2]))
            properties.append(LabelValue(os.environ.get("WEBSITE_HOSTNAME")))
        elif self.vm_retry and self._get_azure_compute_metadata():
            # VM
            properties.append(
                LabelValue(
                    '{}//{}'.format(
                        self.vm_data.get("vmId", ''),
                        self.vm_data.get("subscriptionId", '')),
                )
            )
            os_type = self.vm_data.get("osType", '')
        else:
            # Not in any rp or VM metadata failed
            return None
        
        properties.append(LabelValue("sdk"))  # attach type
        properties.append(LabelValue(self._instrumentation_key))  # cikey
        properties.append(LabelValue(platform.python_version()))  # runTimeVersion
        properties.append(LabelValue(os_type or platform.system()))  # os
        properties.append(LabelValue("python"))  # language
        properties.append(
            LabelValue(azure_monitor_context['ai.internal.sdkVersion']))  # version
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
