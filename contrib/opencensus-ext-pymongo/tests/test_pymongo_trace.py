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

from opencensus.ext.pymongo import trace


class Test_pymongo_trace(unittest.TestCase):

    def test_trace_integration(self):
        mock_register = mock.Mock()

        patch = mock.patch(
            'pymongo.monitoring.register',
            side_effect=mock_register)

        with patch:
            trace.trace_integration()

        self.assertTrue(mock_register.called)

    def test_started(self):
        mock_tracer = MockTracer()

        patch = mock.patch(
            'opencensus.trace.execution_context.get_opencensus_tracer',
            return_value=mock_tracer)

        command_attrs = {
            'filter': 'filter',
            'sort': 'sort',
            'limit': 'limit',
            'command_name': 'find'
        }

        expected_attrs = {
            'filter': 'filter',
            'sort': 'sort',
            'limit': 'limit',
            'request_id': 'request_id',
            'connection_id': 'connection_id'
        }

        expected_name = 'pymongo.database_name.find.command_name'

        with patch:
            trace.MongoCommandListener().started(
                event=MockEvent(command_attrs))

        self.assertEqual(mock_tracer.current_span.attributes, expected_attrs)
        self.assertEqual(mock_tracer.current_span.name, expected_name)

    def test_succeed(self):
        mock_tracer = MockTracer()
        mock_tracer.start_span()

        patch = mock.patch(
            'opencensus.trace.execution_context.get_opencensus_tracer',
            return_value=mock_tracer)

        expected_attrs = {'status': 'succeeded'}

        with patch:
            trace.MongoCommandListener().succeeded(event=MockEvent(None))

        self.assertEqual(mock_tracer.current_span.attributes, expected_attrs)
        mock_tracer.end_span.assert_called_with()

    def test_failed(self):
        mock_tracer = MockTracer()
        mock_tracer.start_span()

        patch = mock.patch(
            'opencensus.trace.execution_context.get_opencensus_tracer',
            return_value=mock_tracer)

        expected_attrs = {'status': 'failed'}

        with patch:
            trace.MongoCommandListener().failed(event=MockEvent(None))

        self.assertEqual(mock_tracer.current_span.attributes, expected_attrs)
        mock_tracer.end_span.assert_called_with()


class MockCommand(object):
    def __init__(self, command_attrs):
        self.command_attrs = command_attrs

    def get(self, key, default=None):
        return self.command_attrs[key] \
            if key in self.command_attrs else default


class MockEvent(object):
    def __init__(self, command_attrs):
        self.command = MockCommand(command_attrs)

    def __getattr__(self, item):
        return item


class MockTracer(object):
    def __init__(self):
        self.current_span = None
        self.end_span = mock.Mock()

    def start_span(self, name=None):
        span = mock.Mock()
        span.name = name
        span.attributes = {}
        self.current_span = span
        return span

    def add_attribute_to_current_span(self, key, value):
        self.current_span.attributes[key] = value
