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

from opencensus.ext.dbapi import trace


class TestDBAPITrace(unittest.TestCase):
    def test_wrap_conn(self):
        wrap_func_name = 'wrap func'
        cursor_func_name = 'cursor_func'

        def mock_wrap(func):
            return wrap_func_name

        mock_func = mock.Mock()
        mock_return = mock.Mock()
        mock_cursor_func = mock.Mock()
        mock_cursor_func.__name__ = cursor_func_name
        mock_return.cursor = mock_cursor_func
        mock_func.return_value = mock_return
        wrapped = trace.wrap_conn(mock_func)

        patch_wrap = mock.patch(
            'opencensus.ext.dbapi.trace.wrap_cursor',
            side_effect=mock_wrap)

        with patch_wrap:
            wrapped()

        self.assertEqual(wrapped.__class__.__name__, 'function')
        self.assertEqual(
            getattr(mock_return, cursor_func_name, None), wrap_func_name)

    def test_wrap_cursor(self):
        wrap_func_name = 'wrap func'

        def mock_trace_cursor_query(func):
            return wrap_func_name + func.__name__

        mock_func = mock.Mock()
        mock_return = mock.Mock()

        for func in trace.QUERY_WRAP_METHODS:
            query_func = mock.Mock()
            query_func.__name__ = func
            setattr(mock_return, func, query_func)

        mock_func.return_value = mock_return

        wrapped = trace.wrap_cursor(mock_func)

        patch_wrap = mock.patch(
            'opencensus.ext.dbapi.trace.trace_cursor_query',
            side_effect=mock_trace_cursor_query)

        with patch_wrap:
            wrapped()

        for func in trace.QUERY_WRAP_METHODS:
            self.assertEqual(
                getattr(mock_return, func, None), wrap_func_name + func)

    def test_trace_cursor_query(self):
        return_value = 'trace test'
        query = 'SELECT 1'
        mock_func = mock.Mock()
        mock_func.__name__ = 'execute'
        mock_func.return_value = return_value
        mock_tracer = mock.Mock()
        mock_cursor = mock.Mock()

        patch = mock.patch(
            'opencensus.ext.dbapi.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)

        wrapped = trace.trace_cursor_query(mock_func)

        with patch:
            result = wrapped(mock_cursor, query)

        self.assertEqual(result, return_value)
        self.assertTrue(mock_tracer.start_span.called)
        self.assertTrue(mock_tracer.add_attribute_to_current_span.called)
        self.assertTrue(mock_tracer.end_span.called)
