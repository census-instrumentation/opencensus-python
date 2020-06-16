# Copyright 2018, OpenCensus Authors
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

from opencensus.common.transports import base
from opencensus.trace import execution_context


class SyncTransport(base.Transport):
    def __init__(self, exporter):
        self.exporter = exporter

    def export(self, datas):
        # Used to suppress tracking of requests in export
        execution_context.set_is_exporter(True)
        self.exporter.emit(datas)
        # Reset the context
        execution_context.set_is_exporter(False)
