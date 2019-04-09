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
from opencensus.common.version import __version__ as opencensus_version
from opencensus.ext.azure.protocol import Object
from opencensus.ext.azure.version import __version__ as extension_version

azure_monitor_context = {
    'ai.cloud.role': os.path.basename(sys.argv[0]) or 'Python Application',  # TODO
    'ai.cloud.roleInstance': platform.node(),
    'ai.device.id': platform.node(),
    'ai.device.locale': locale.getdefaultlocale()[0],
    'ai.device.osVersion': platform.version(),
    'ai.device.type': 'Other',
    'ai.internal.sdkVersion': 'py{}:oc{}:ext{}'.format(
        platform.python_version(),
        opencensus_version,
        extension_version,
    ),
}

def microseconds_to_duration(microseconds):
    n = (microseconds + 500) // 1000  # duration in milliseconds
    ms = n % 1000  # millisecond
    n = n // 1000
    s = n % 60  # second
    n = n // 60
    m = n % 60  # minute
    n = n // 60
    h = n % 24  # hour
    d = n // 24  # day
    return '{:d}.{:02d}:{:02d}:{:02d}.{:03d}'.format(d, h, m, s, ms)


class Config(Object):
    prototype = Object(
        endpoint='https://dc.services.visualstudio.com/v2/track',
        instrumentation_key=None,
    )
