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

"""Export the trace spans by printing them out."""

from opencensus.trace.exporters import base
from opencensus.trace.exporters.transports import sync


class PrintExporter(base.Exporter):
    """Export the spans by printing them.

    :type transport: :class:`type`
    :param transport: Class for creating new transport objects. It should
                      extend from the base :class:`.Transport` type and
                      implement :meth:`.Transport.export`. Defaults to
                      :class:`.SyncTransport`. The other option is
                      :class:`.BackgroundThreadTransport`.
    """
    def __init__(self, transport=sync.SyncTransport):
        self.transport = transport(self)

    def emit(self, trace):
        """export the traces by printing it out.

        :type trace: dict
        :param trace: Trace collected.

        :rtype: dict
        :returns: Trace printed.
        """
        print(trace)
        return trace

    def export(self, trace):
        self.transport.export(trace)
