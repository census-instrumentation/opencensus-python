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
from collections import OrderedDict

from opencensus.common.version import __version__ as opencensus_version
from opencensus.ext.azure.common.version import __version__ as ext_version
from opencensus.metrics.export.gauge import LongGauge
from opencensus.metrics.label_key import LabelKey
from opencensus.metrics.label_value import LabelValue


class HeartbeatMetric:
    NAME = "Heartbeat"

    def __init__(self):
        self.properties = OrderedDict()
        self.properties[LabelKey("sdk", '')] = LabelValue(
                'py{}:oc{}:ext{}'.format(
                platform.python_version(),
                opencensus_version,
                ext_version,
            )
        )
        self.properties[LabelKey("osType", '')] = LabelValue(platform.system())
        if os.environ.get("WEBSITE_SITE_NAME") is not None:  # Web apps
            self.properties[LabelKey("appSrv_SiteName", '')] = LabelValue(os.environ.get("WEBSITE_SITE_NAME"))
            self.properties[LabelKey("appSrv_wsStamp", '')] = LabelValue(os.environ.get("WEBSITE_HOME_STAMPNAME", ''))
            self.properties[LabelKey("appSrv_wsHost", '')] = LabelValue(os.environ.get("WEBSITE_HOSTNAME", ''))
        elif os.environ.get("FUNCTIONS_WORKER_RUNTIME") is not None:  # Function apps
            self.properties[LabelKey("azfunction_appId", '')] = LabelValue(os.environ.get("WEBSITE_HOSTNAME"))

    def __call__(self):
        """ Returns a derived gauge for the heartbeat metric.

        :rtype: :class:`opencensus.metrics.export.gauge.LongGauge`
        :return: The gauge representing the heartbeat metric
        """
        gauge = LongGauge(
            HeartbeatMetric.NAME,
            'Heartbeat metric with custom dimensions',
            'count',
            list(self.properties.keys()))
        gauge.get_or_create_time_series(list(self.properties.values()))
        return gauge
