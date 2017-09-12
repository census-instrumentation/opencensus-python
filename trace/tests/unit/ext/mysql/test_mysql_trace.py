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

from opencensus.trace.ext.mysql import trace


class Test_mysql_trace(unittest.TestCase):

    def test_trace_integration(self):

        def mock_wrap(func):
            return 'mock call'

        mock_call = 'mock call'
        mock_inspect = mock.Mock()
        mock_mysql_module = mock.Mock()

        mock_inspect.getmodule.return_value = mock_mysql_module

        patch_wrap = mock.patch(
            'opencensus.trace.ext.mysql.trace.wrap_conn',
            side_effect=mock_wrap)
        patch_inspect = mock.patch(
            'opencensus.trace.ext.mysql.trace.inspect',
            mock_inspect)

        with patch_wrap, patch_inspect:
            trace.trace_integration()

        self.assertEqual(mock_mysql_module.connect, mock_call)

    def test_wrap_conn(self):
        mock_func = mock.Mock()
        wrapped = trace.wrap_conn(mock_func)

        patch = mock.patch.object(
            trace.TraceConnection,
            '__init__',
            lambda x, y: None, None)

        with patch:
            call_result = wrapped()

        self.assertEqual(wrapped.__class__.__name__, 'function')
        assert isinstance(call_result, trace.TraceConnection)


class TestTraceConnection(unittest.TestCase):

    def test_constructor(self):
        conn = mock.Mock()
        connection = trace.TraceConnection(conn=conn)

        self.assertIs(connection._conn, conn)

    def test_cursor(self):
        conn = mock.Mock()
        connection = trace.TraceConnection(conn=conn)

        cursor = connection.cursor()

        assert isinstance(cursor, trace.TraceCursor)


class TestTraceCursor(unittest.TestCase):

    def test_constructor(self):
        from opencensus.trace.tracer import noop_tracer

        mock_cursor = mock.Mock()
        cursor = trace.TraceCursor(mock_cursor)

        self.assertEqual(cursor._cursor, mock_cursor)
        assert isinstance(cursor._tracer, noop_tracer.NoopTracer)

    def test__trace_cursor_query(self):
        query = 'SELECT 1'

        def test_method(query, *args, **kwargs):
            return query

        mock_cursor = mock.Mock()
        mock_tracer = mock.Mock()

        cursor = trace.TraceCursor(mock_cursor)
        cursor._tracer = mock_tracer
        result = cursor._trace_cursor_query(test_method, query, query)

        self.assertEqual(result, query)
        self.assertTrue(mock_tracer.start_span.called)
        self.assertTrue(mock_tracer.add_label_to_current_span.called)
        self.assertTrue(mock_tracer.end_span.called)

    def test_execute(self):
        query = 'SELECT 1'

        def execute(query, *args, **kwargs):
            return query

        mock_cursor = mock.Mock()
        mock_tracer = mock.Mock()

        mock_cursor.execute = execute

        cursor = trace.TraceCursor(mock_cursor)
        cursor.tracer = mock_tracer

        cursor.execute(query)

        self.assertTrue(mock_cursor.execute)

    def test_executemany(self):
        query = 'SELECT 1'

        def executemany(query, *args, **kwargs):
            return query

        mock_cursor = mock.Mock()
        mock_tracer = mock.Mock()

        mock_cursor.executemany = executemany

        cursor = trace.TraceCursor(mock_cursor)
        cursor.tracer = mock_tracer

        cursor.executemany(query)

        self.assertTrue(mock_cursor.executemany)
