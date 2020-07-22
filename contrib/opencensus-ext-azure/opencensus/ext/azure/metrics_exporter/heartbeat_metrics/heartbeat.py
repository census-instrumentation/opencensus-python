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
from collections import OrderedDict

from opencensus.common.version import __version__ as opencensus_version
from opencensus.ext.azure.common.version import __version__ as ext_version
from opencensus.metrics.export.gauge import LongGauge
from opencensus.metrics.label_key import LabelKey
from opencensus.metrics.label_value import LabelValue


_AIMS_URI = "http://169.254.169.254/metadata/instance/compute"
_AIMS_API_VERSION = "api-version=2017-12-01"
_AIMS_FORMAT = "format=json"


class HeartbeatMetric:
    NAME = "Heartbeat"

    def __init__(self):
        self.vm_data = {}
        self.is_vm = False
        self.properties = OrderedDict()
        self.update_properties()
        self.heartbeat = LongGauge(
            HeartbeatMetric.NAME,
            'Heartbeat metric with custom dimensions',
            'count',
            list(self.properties.keys()),
        )
        self.heartbeat.get_or_create_time_series(
            list(self.properties.values())
        )

    def get_metrics(self):
        if self.is_vm:
            # Only need to update if in vm (properties could change)
            self.properties.clear()
            self.update_properties()
            self.heartbeat.clear()
            # pylint: disable=protected-access
            self.heartbeat.descriptor._label_keys = \
                list(self.properties.keys())
            self.heartbeat._len_label_keys = len(list(self.properties.keys()))
            self.heartbeat.get_or_create_time_series(
                list(self.properties.values())
            )
        return [self.heartbeat.get_metric(datetime.datetime.utcnow())]

    def update_properties(self):
        self.properties[LabelKey("sdk", '')] = LabelValue(
            'py{}:oc{}:ext{}'.format(
                platform.python_version(),
                opencensus_version,
                ext_version,
            )
        )
        self.properties[LabelKey("osType", '')] = LabelValue(platform.system())
        if os.environ.get("WEBSITE_SITE_NAME") is not None:
            # Web apps
            self.properties[LabelKey("appSrv_SiteName", '')] = \
                LabelValue(os.environ.get("WEBSITE_SITE_NAME"))
            self.properties[LabelKey("appSrv_wsStamp", '')] = \
                LabelValue(os.environ.get("WEBSITE_HOME_STAMPNAME", ''))
            self.properties[LabelKey("appSrv_wsHost", '')] = \
                LabelValue(os.environ.get("WEBSITE_HOSTNAME", ''))
        elif os.environ.get("FUNCTIONS_WORKER_RUNTIME") is not None:
            # Function apps
            self.properties[LabelKey("azfunction_appId", '')] = \
                LabelValue(os.environ.get("WEBSITE_HOSTNAME"))
        elif self.get_azure_compute_metadata():
            # VM
            if self.vm_data:
                self.properties[LabelKey("azInst_vmId", '')] = \
                    LabelValue(self.vm_data.get("vmId", ''))
                self.properties[LabelKey("azInst_subscriptionId", '')] = \
                    LabelValue(self.vm_data.get("subscriptionId", ''))
                self.properties[LabelKey("azInst_osType", '')] = \
                    LabelValue(self.vm_data.get("osType", ''))   

    def get_azure_compute_metadata(self):
        try:
            request_url = "{0}?{1}&{2}".format(_AIMS_URI, _AIMS_API_VERSION, _AIMS_FORMAT)
            response = requests.get(request_url, headers={"MetaData":"True"})
        except requests.exceptions.ConnectionError:
            # Not in VM
            self.is_vm = False
            return False
        
        self.is_vm = True
        try:
            text = response.text
            self.vm_data = json.loads(text)
        except Exception:  # pylint: disable=broad-except
            # Error in reading response body, retry
            pass

        return True
