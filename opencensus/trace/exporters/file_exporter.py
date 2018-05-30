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
import pickle

from opencensus.trace import span_data
from opencensus.trace.exporters import base
from opencensus.trace.exporters.transports import sync

DEFAULT_FILENAME = 'opencensus-traces'


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

    :type file_format: str
    :param file_format: The file format of output file. Defaults to 'json'.
                        Another option is 'pkl' which is a serialized binary
                        pickle file and it can be unpacked with pickle.load().
    """

    def __init__(self, file_name=DEFAULT_FILENAME,
                 transport=sync.SyncTransport,
                 file_mode='w+',
                 file_format='json'):

        if not (file_format in ['json', 'pkl']):  # pragma: NO COVER
            raise Exception('Unsupported file format')

        if file_format == 'pkl':
            file_mode = 'wb'

        if file_name == DEFAULT_FILENAME:
            file_name = '{}.{}'.format(file_name, file_format)

        self.file_name = file_name
        self.file_format = file_format
        self.transport = transport(self)
        self.file_mode = file_mode

    def emit(self, span_datas):
        """
        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param list of opencensus.trace.span_data.SpanData span_datas:
            SpanData tuples to emit
        """
        with open(self.file_name, self.file_mode) as f:
            if self.file_format == 'json':
                trace_json = span_data.format_legacy_trace_json(span_datas)
                f.write(json.dumps(trace_json))
            else:
                pickle.dump(span_datas, f)

    def export(self, span_datas):
        """
        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param list of opencensus.trace.span_data.SpanData span_datas:
            SpanData tuples to export
        """
        self.transport.export(span_datas)
