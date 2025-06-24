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

import os
import tempfile
import unittest

import json
import mock

from opencensus.trace import file_exporter


class TestFileExporter(unittest.TestCase):

    def test_constructor(self):
        _, file_name = tempfile.mkstemp()
        exporter = file_exporter.FileExporter(file_name=file_name)
        self.assertEqual(exporter.file_name, file_name)

    def test_emit_empty(self):
        traces = {}
        _, file_name = tempfile.mkstemp()
        exporter = file_exporter.FileExporter(file_name=file_name)
        exporter.emit(traces)
        self.assertTrue(os.path.exists(file_name))

    def test_emit(self):
        mock_formatted_trace = {
            'traceId': 'traceId',
            'spans': [{
                'displayName': 'displayName',
                'spanId': 'spanId',
                'startTime': 'startTime',
                'endTime': 'endTime',
                'childSpanCount': 'childSpanCount',
                'kind': 'kind'
            }]
        }
        mock_format = mock.patch(
            'opencensus.trace.file_exporter'
            '.span_data.format_legacy_trace_json',
            return_value=mock_formatted_trace)

        _, file_name = tempfile.mkstemp()
        exporter = file_exporter.FileExporter(file_name=file_name)

        with mock_format:
            exporter.emit(mock.Mock())

        self.assertTrue(os.path.exists(file_name))
        self.assertEqual(json.loads(open(file_name).read().strip()),
                         mock_formatted_trace)
        self.assertEqual(len(open(file_name).readlines()), 1)

        with mock_format:
            exporter.emit(mock.Mock())
            exporter.emit(mock.Mock())

        self.assertEqual(len(open(file_name).readlines()), 3)

    def test_export(self):
        file_name = 'file_name'
        exporter = file_exporter.FileExporter(file_name=file_name,
                                              transport=MockTransport)

        exporter.export({})

        self.assertTrue(exporter.transport.export_called)


class MockTransport(object):
    def __init__(self, exporter=None):
        self.export_called = False
        self.exporter = exporter

    def export(self, trace):
        self.export_called = True
