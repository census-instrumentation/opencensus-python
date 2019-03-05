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

from opencensus.ext.postgresql import trace


class Test_postgresql_trace(unittest.TestCase):
    def test_trace_integration(self):
        mock_return = 'test connect'

        def mock_connect():
            return mock_return

        mock_inspect = mock.Mock()
        mock_postgresql_module = mock.Mock()
        mock_inspect.getmodule.return_value = mock_postgresql_module

        patch_connect = mock.patch(
            'opencensus.ext.postgresql.trace.connect',
            side_effect=mock_connect)
        patch_inspect = mock.patch(
            'opencensus.ext.postgresql.trace.inspect', mock_inspect)

        with patch_connect, patch_inspect:
            trace.trace_integration()

        return_value = mock_postgresql_module.connect()

        self.assertIsNotNone(mock_postgresql_module.connect)
        self.assertEqual(return_value, mock_return)

    def test_connect(self):
        mock_pg_connect = mock.Mock()
        return_conn = 'postgre conn'
        mock_pg_connect.return_value = return_conn
        mock_cursor = mock.Mock(spec=trace.TraceCursor)
        patch_connect = mock.patch(
            'opencensus.ext.postgresql.trace.pg_connect',
            mock_pg_connect)
        patch_cursor = mock.patch(
            'opencensus.ext.postgresql.trace.TraceCursor', mock_cursor)

        with patch_connect, patch_cursor:
            trace.connect()

        mock_pg_connect.assert_called_once_with(cursor_factory=mock_cursor)

    def test_trace_cursor_query(self):
        return_value = 'trace test'
        query = 'SELECT 1'
        mock_func = mock.Mock()
        mock_func.__name__ = 'execute'
        mock_func.return_value = return_value
        mock_tracer = mock.Mock()

        patch = mock.patch(
            'opencensus.ext.postgresql.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)

        wrapped = trace.trace_cursor_query(mock_func)

        with patch:
            result = wrapped(query)

        self.assertEqual(result, return_value)
        self.assertTrue(mock_tracer.start_span.called)
        self.assertTrue(mock_tracer.add_attribute_to_current_span.called)
        self.assertTrue(mock_tracer.end_span.called)

    def test_trace_cursor_query_none_tracer(self):
        return_value = 'trace test'
        query = 'SELECT 1'
        mock_func = mock.Mock()
        mock_func.__name__ = 'execute'
        mock_func.return_value = return_value
        mock_tracer = mock.Mock()

        patch = mock.patch(
            'opencensus.ext.postgresql.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=None)

        wrapped = trace.trace_cursor_query(mock_func)

        with patch:
            result = wrapped(query)

        self.assertEqual(result, return_value)
        self.assertFalse(mock_tracer.start_span.called)
        self.assertFalse(mock_tracer.add_attribute_to_current_span.called)
        self.assertFalse(mock_tracer.end_span.called)


class TestTraceCursor(unittest.TestCase):
    def test_constructor(self):
        wrap_func_name = 'wrap func: '

        def mock_trace_cursor_query(func):
            return wrap_func_name + func.__name__

        def mock___init__(cursor):
            for func in trace.QUERY_WRAP_METHODS:
                query_func = getattr(cursor, func)
                wrapped = cursor.trace_cursor_query(query_func)
                setattr(cursor, query_func.__name__, wrapped)

        mock_cursor = mock.Mock()
        mock_cursor.trace_cursor_query.side_effect = mock_trace_cursor_query

        for func in trace.QUERY_WRAP_METHODS:
            query_func = mock.Mock()
            query_func.__name__ = func
            setattr(mock_cursor, func, query_func)

        patch_init = mock.patch.object(
            trace.TraceCursor, '__init__', side_effect=mock___init__)

        with patch_init:
            trace.TraceCursor(mock_cursor)

        for func in trace.QUERY_WRAP_METHODS:
            self.assertEqual(
                getattr(mock_cursor, func, None), wrap_func_name + func)
