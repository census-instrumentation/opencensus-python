# Copyright 2017, OpenCensus Authors
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

"""Export the trace spans to a local file."""

import json

from opencensus.trace.exporters import base
from opencensus.trace.exporters.transports import sync

DEFAULT_FILENAME = 'opencensus-traces.json'


class FileExporter(base.Exporter):
    """
    :type file_name: str
    :param file_name: The name of the output file.

    :type transport: :class:`type`
    :param transport: Class for creating new transport objects. It should
                      extend from the base :class:`.Transport` type and
                      implement :meth:`.Transport.export`. Defaults to
                      :class:`.SyncTransport`. The other option is
                      :class:`.BackgroundThreadTransport`.

    :type file_mode: str
    :param file_mode: The file mode to open the output file with.
                      Defaults to w+

    """

    def __init__(self, file_name=DEFAULT_FILENAME,
                 transport=sync.SyncTransport,
                 file_mode='w+'):
        self.file_name = file_name
        self.transport = transport(self)
        self.file_mode = file_mode

    def emit(self, trace):
        """
        :type trace: dict
        :param trace: Trace collected.
        """
        with open(self.file_name, self.file_mode) as file:
            trace_str = json.dumps(trace)
            file.write(trace_str)

    def export(self, trace):
        self.transport.export(trace)
