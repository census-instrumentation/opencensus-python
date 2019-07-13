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
import sys

from opencensus.ext.azure.common.protocol import BaseObject


class Options(BaseObject):
    _default = BaseObject(
        enable_standard_metrics=True,
        endpoint='https://dc.services.visualstudio.com/v2/track',
        export_interval=15.0,
        grace_period=5.0,
        instrumentation_key=os.getenv('APPINSIGHTS_INSTRUMENTATIONKEY', None),
        max_batch_size=100,
        minimum_retry_interval=60,  # minimum retry interval in seconds
        proxy=None,
        storage_maintenance_period=60,
        storage_max_size=100*1024*1024,
        storage_path=os.path.join(
            os.path.expanduser('~'),
            '.opencensus',
            '.azure',
            os.path.basename(sys.argv[0]) or '.console',
        ),
        storage_retention_period=7*24*60*60,
        timeout=10.0,  # networking timeout in seconds
    )
