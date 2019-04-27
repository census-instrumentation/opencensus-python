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

from opencensus.ext.azure.common.protocol import Object


class Options(Object):
    prototype = Object(
        endpoint='https://dc.services.visualstudio.com/v2/track',
        instrumentation_key=os.getenv('APPINSIGHTS_INSTRUMENTATIONKEY', None),
        minimum_retry_interval=60,  # minimum retry interval in seconds
        proxy=None,
        storage_maintenance_period=60,
        storage_path='.azure',
        timeout=5.0,  # networking timeout in seconds
    )
