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

import platform
import locale
from opencensus.common.version import __version__ as opencensus_version
from opencensus.ext.azure.version import __version__ as extension_version

exporter_version = '0.1.dev0'

azure_monitor_context = {
    'ai.device.id': platform.node(),
    'ai.device.locale': locale.getdefaultlocale()[0],
    'ai.device.osVersion': platform.version(),
    'ai.device.type': 'Other',
    'ai.internal.sdkVersion': 'py{}:{}:{}'.format(
        platform.python_version(),
        opencensus_version,
        extension_version,
    ),
}
