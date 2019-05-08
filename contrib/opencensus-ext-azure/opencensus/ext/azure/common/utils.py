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

import locale
import os
import platform
import sys

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from opencensus.common.version import __version__ as opencensus_version
from opencensus.common.utils import timestamp_to_microseconds
from opencensus.ext.azure.common.version import __version__ as ext_version

azure_monitor_context = {
    'ai.cloud.role': os.path.basename(sys.argv[0]) or 'Python Application',
    'ai.cloud.roleInstance': platform.node(),
    'ai.device.id': platform.node(),
    'ai.device.locale': locale.getdefaultlocale()[0],
    'ai.device.osVersion': platform.version(),
    'ai.device.type': 'Other',
    'ai.internal.sdkVersion': 'py{}:oc{}:ext{}'.format(
        platform.python_version(),
        opencensus_version,
        ext_version,
    ),
}


def microseconds_to_duration(microseconds):
    n = (microseconds + 500) // 1000  # duration in milliseconds
    n, ms = divmod(n, 1000)
    n, s = divmod(n, 60)
    n, m = divmod(n, 60)
    d, h = divmod(n, 24)
    return '{:d}.{:02d}:{:02d}:{:02d}.{:03d}'.format(d, h, m, s, ms)


def timestamp_to_duration(start_time, end_time):
    start_time_us = timestamp_to_microseconds(start_time)
    end_time_us = timestamp_to_microseconds(end_time)
    duration_us = int(end_time_us - start_time_us)
    return microseconds_to_duration(duration_us)


def url_to_dependency_name(url):
    return urlparse(url).netloc
