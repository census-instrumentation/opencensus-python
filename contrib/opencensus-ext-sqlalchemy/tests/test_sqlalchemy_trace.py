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

import unittest

import mock

from opencensus.trace import span as span_module
from opencensus.ext.sqlalchemy import trace


class Test_sqlalchemy_trace(unittest.TestCase):

    def test_trace_integration(self):
        mock_trace_engine = mock.Mock()

        patch = mock.patch(
            'opencensus.ext.sqlalchemy.trace.trace_engine',
            side_effect=mock_trace_engine)

        with patch:
            trace.trace_integration()

        self.assertTrue(mock_trace_engine.called)

    def test_trace_engine(self):
        mock_listen = mock.Mock()
        mock_engine = mock.Mock()
        mock_before = mock.Mock()
        mock_after = mock.Mock()

        patch_listen = mock.patch(
            'opencensus.ext.sqlalchemy.trace.event.listen',
            side_effect=mock_listen)
        patch_before = mock.patch(
            'opencensus.ext.sqlalchemy.trace._before_cursor_execute',
            side_effect=mock_before)
        patch_after = mock.patch(
            'opencensus.ext.sqlalchemy.trace._after_cursor_execute',
            side_effect=mock_after)

        with patch_listen, patch_before, patch_after:
            trace.trace_engine(mock_engine)

        self.assertTrue(mock_listen.called)

    def test__before_cursor_execute(self):
        mock_tracer = MockTracer()

        patch = mock.patch(
            'opencensus.ext.sqlalchemy.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)

        query = 'SELECT * FROM employee'
        parameters = 'test'

        with patch:
            trace._before_cursor_execute(None, None, query,
                                         parameters, None, False)

        expected_attributes = {
            'sqlalchemy.query': query,
            'sqlalchemy.query.parameters': parameters,
            'sqlalchemy.cursor.method.name': 'execute'
        }

        expected_name = 'sqlalchemy.query'

        self.assertEqual(mock_tracer.current_span.span_kind,
                         span_module.SpanKind.CLIENT)
        self.assertEqual(mock_tracer.current_span.attributes,
                         expected_attributes)
        self.assertEqual(mock_tracer.current_span.name, expected_name)

    def test__before_cursor_executemany(self):
        mock_tracer = MockTracer()

        patch = mock.patch(
            'opencensus.ext.sqlalchemy.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)

        query = 'SELECT * FROM employee'
        parameters = 'test'

        with patch:
            trace._before_cursor_execute(None, None, query,
                                         parameters, None, True)

        expected_attributes = {
            'sqlalchemy.query': query,
            'sqlalchemy.query.parameters': parameters,
            'sqlalchemy.cursor.method.name': 'executemany'
        }

        expected_name = 'sqlalchemy.query'

        self.assertEqual(mock_tracer.current_span.attributes,
                         expected_attributes)
        self.assertEqual(mock_tracer.current_span.name, expected_name)

    def test__after_cursor_execute(self):
        mock_tracer = mock.Mock()

        patch = mock.patch(
            'opencensus.ext.sqlalchemy.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)

        with patch:
            trace._after_cursor_execute(None, None, None, None, None, None)

        self.assertTrue(mock_tracer.end_span.called)


class MockTracer(object):
    def __init__(self):
        self.current_span = None

    def start_span(self):
        span = mock.Mock()
        span.attributes = {}
        self.current_span = span
        return span

    def add_attribute_to_current_span(self, key, value):
        self.current_span.attributes[key] = value
