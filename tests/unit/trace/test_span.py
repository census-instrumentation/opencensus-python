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

import datetime
import unittest

import mock

from google.rpc import code_pb2

from opencensus.common import utils
from opencensus.trace.stack_trace import StackTrace
from opencensus.trace.status import Status
from opencensus.trace.time_event import TimeEvent


class TestSpan(unittest.TestCase):

    project = 'PROJECT'

    @staticmethod
    def _get_target_class():
        from opencensus.trace.span import Span

        return Span

    def _make_one(self, *args, **kw):
        return self._get_target_class()(*args, **kw)

    def test_constructor_defaults(self):
        span_id = 'test_span_id'
        span_name = 'test_span_name'

        patch = mock.patch(
            'opencensus.trace.span.generate_span_id', return_value=span_id)

        with patch:
            span = self._make_one(span_name)

        self.assertEqual(span.name, span_name)
        self.assertEqual(span.span_id, span_id)
        self.assertIsNone(span.parent_span)
        self.assertEqual(span.attributes, {})
        self.assertIsNone(span.start_time)
        self.assertIsNone(span.end_time)
        self.assertEqual(span.children, [])
        self.assertIsNone(span.context_tracer)

    def test_constructor_explicit(self):

        span_id = 'test_span_id'
        span_name = 'test_span_name'
        parent_span = mock.Mock()
        start_time = utils.to_iso_str()
        end_time = utils.to_iso_str()
        attributes = {
            'http.status_code': '200',
            'component': 'HTTP load balancer',
        }
        time_events = mock.Mock()
        links = mock.Mock()
        stack_trace = mock.Mock()
        status = mock.Mock()
        context_tracer = mock.Mock()

        span = self._make_one(
            name=span_name,
            parent_span=parent_span,
            attributes=attributes,
            start_time=start_time,
            end_time=end_time,
            span_id=span_id,
            stack_trace=stack_trace,
            time_events=time_events,
            links=links,
            status=status,
            context_tracer=context_tracer)

        self.assertEqual(span.name, span_name)
        self.assertEqual(span.span_id, span_id)
        self.assertEqual(span.parent_span, parent_span)
        self.assertEqual(span.attributes, attributes)
        self.assertEqual(span.start_time, start_time)
        self.assertEqual(span.end_time, end_time)
        self.assertEqual(span.time_events, time_events)
        self.assertEqual(span.stack_trace, stack_trace)
        self.assertEqual(span.links, links)
        self.assertEqual(span.status, status)
        self.assertEqual(span.children, [])
        self.assertEqual(span.context_tracer, context_tracer)

    def test_span(self):
        span_id = 'test_span_id'
        root_span_name = 'root_span'
        child_span_name = 'child_span'
        root_span = self._make_one(root_span_name)
        root_span._child_spans = []

        patch = mock.patch(
            'opencensus.trace.span.generate_span_id', return_value=span_id)

        with patch:
            with root_span:
                root_span.span(child_span_name)

        self.assertEqual(len(root_span._child_spans), 1)

        result_child_span = root_span._child_spans[0]

        self.assertEqual(result_child_span.name, child_span_name)
        self.assertEqual(result_child_span.span_id, span_id)
        self.assertEqual(result_child_span.parent_span, root_span)
        self.assertEqual(result_child_span.attributes, {})
        self.assertIsNone(result_child_span.start_time)
        self.assertIsNone(result_child_span.end_time)

    def test_add_attribute(self):
        span_name = 'test_span_name'
        span = self._make_one(span_name)
        attribute_key = 'attribute_key'
        attribute_value = 'attribute_value'
        span.add_attribute(attribute_key, attribute_value)

        self.assertEqual(span.attributes[attribute_key], attribute_value)
        span.attributes.pop(attribute_key, None)

    def test_add_time_event(self):
        from opencensus.trace.time_event import TimeEvent

        span_name = 'test_span_name'
        span = self._make_one(span_name)
        time_event = mock.Mock()

        with self.assertRaises(TypeError):
            span.add_time_event(time_event)

        time_event = TimeEvent(datetime.datetime.utcnow())
        span.add_time_event(time_event)

        self.assertEqual(len(span.time_events), 1)

    def test_add_annotation(self):
        span_name = 'test_span_name'
        span = self._make_one(span_name)

        span.add_annotation('This is a test', name='octo-span', age=98)

        self.assertEqual(len(span.time_events), 1)
        a0 = span.time_events[0].annotation
        self.assertEqual(a0.description, 'This is a test')
        self.assertEqual(a0.attributes.attributes,
                         dict(name='octo-span', age=98))

    def test_add_link(self):
        from opencensus.trace.link import Link

        span_name = 'test_span_name'
        span = self._make_one(span_name)
        link = mock.Mock()

        with self.assertRaises(TypeError):
            span.add_link(link)

        link = Link(span_id='1234', trace_id='4567')
        span.add_link(link)

        self.assertEqual(len(span.links), 1)

    def test_start(self):
        span_name = 'root_span'
        span = self._make_one(span_name)
        self.assertIsNone(span.start_time)

        span.start()
        self.assertIsNotNone(span.start_time)

    def test_finish_without_context_tracer(self):
        span_name = 'root_span'
        span = self._make_one(span_name)
        self.assertIsNone(span.end_time)

        span.finish()
        self.assertIsNotNone(span.end_time)

    def test_finish_with_context_tracer(self):
        context_tracer = mock.Mock()
        span_name = 'root_span'
        span = self._make_one(name=span_name, context_tracer=context_tracer)

        with span:
            print('test')

        self.assertTrue(context_tracer.end_span.called)

    def test_finish(self):
        span_name = 'root_span'
        span = self._make_one(span_name)
        self.assertIsNone(span.end_time)

        span.finish()
        self.assertIsNotNone(span.end_time)

    def test_on_create(self):
        from opencensus.trace.span import Span
        self.on_create_called = False
        self._make_one('span1')
        self.assertFalse(self.on_create_called)
        try:

            @Span.on_create
            def callback(span):
                self.on_create_called = True

            self._make_one('span2')
        finally:
            Span._on_create_callbacks = []
        self.assertTrue(self.on_create_called)
        del self.on_create_called

    def test___iter__(self):
        root_span_name = 'root_span_name'
        child1_span_name = 'child1_span_name'
        child2_span_name = 'child2_span_name'
        child1_child1_span_name = 'child1_child1_span_name'

        root_span = self._make_one(root_span_name)
        child1_span = self._make_one(child1_span_name)
        child2_span = self._make_one(child2_span_name)
        child1_child1_span = self._make_one(child1_child1_span_name)

        child1_span._child_spans.append(child1_child1_span)
        root_span._child_spans.extend([child1_span, child2_span])

        span_iter_list = list(iter(root_span))

        self.assertEqual(
            span_iter_list,
            [child1_child1_span, child1_span, child2_span, root_span])

    def test_exception_in_span(self):
        """Make sure that an exception within a span context is
        attached to the span"""
        root_span = self._make_one('root_span')
        exception_message = 'error'
        with self.assertRaises(AssertionError):
            with root_span:
                raise AssertionError(exception_message)
        stack_trace = root_span.stack_trace
        # make sure a stack trace has been attached and populated
        self.assertIsNotNone(stack_trace)
        self.assertIsNotNone(stack_trace.stack_trace_hash_id)
        self.assertEqual(len(stack_trace.stack_frames), 1)

        stack_frame = stack_trace.stack_frames[0]
        self.assertEqual(stack_frame['file_name']['value'], __file__)
        self.assertEqual(stack_frame['function_name']['value'],
                         'test_exception_in_span')
        self.assertEqual(stack_frame['load_module']['module']['value'],
                         __file__)
        self.assertEqual(stack_frame['original_function_name']['value'],
                         'test_exception_in_span')
        self.assertIsNotNone(stack_frame['source_version']['value'])
        self.assertIsNotNone(stack_frame['load_module']['build_id']['value'])

        self.assertIsNotNone(root_span.status)
        self.assertEqual(root_span.status.message, exception_message)
        self.assertEqual(root_span.status.code, code_pb2.UNKNOWN)


class Test_format_span_json(unittest.TestCase):
    def test_format_span_json_no_parent_span(self):
        from opencensus.trace.span import format_span_json

        name = 'test span'
        span_id = 1234
        start_time = '2017-06-25'
        end_time = '2017-06-26'

        span = mock.Mock()
        span.name = name
        span.span_id = span_id
        span.start_time = start_time
        span.end_time = end_time
        span.parent_span = None
        span.attributes = None
        span.stack_trace = None
        span.status = None
        span._child_spans = []
        span.time_events = []
        span.links = []
        span.same_process_as_parent_span = None

        expected_span_json = {
            'spanId': span_id,
            'startTime': start_time,
            'endTime': end_time,
            'displayName': {
                'truncated_byte_count': 0,
                'value': 'test span'
            },
            'childSpanCount': 0,
        }

        span_json = format_span_json(span)
        self.assertEqual(span_json, expected_span_json)

    @mock.patch.object(StackTrace, 'format_stack_trace_json')
    @mock.patch.object(Status, 'format_status_json')
    @mock.patch.object(TimeEvent, 'format_time_event_json')
    def test_format_span_json_with_parent_span(self, time_event_mock,
                                               status_mock, stack_trace_mock):

        from opencensus.trace.link import Link
        from opencensus.trace.span import format_span_json

        name = 'test span'
        span_id = 1234
        trace_id = '3456'
        attributes = {
            'http.status_code': '200',
            'component': 'HTTP load balancer',
            'none_key': None
        }

        links = {
            'link': [
                {
                    'trace_id': trace_id,
                    'span_id': span_id,
                    'type': 0
                },
            ],
        }

        start_time = '2017-06-25'
        end_time = '2017-06-26'
        parent_span = mock.Mock()
        parent_span_id = 5678
        parent_span.span_id = parent_span_id

        span = mock.Mock()
        span.parent_span = parent_span
        span.name = name
        span.attributes = attributes
        span.span_id = span_id
        span.start_time = start_time
        span.end_time = end_time
        span._child_spans = []
        span.time_events = [TimeEvent(datetime.datetime.utcnow())]
        span.stack_trace = StackTrace()
        span.status = Status(code='200', message='test')
        span.links = [Link(trace_id, span_id)]
        span.same_process_as_parent_span = True

        mock_stack_trace = 'stack trace'
        mock_status = 'status'
        mock_time_event = 'time event'

        stack_trace_mock.return_value = mock_stack_trace
        status_mock.return_value = mock_status
        time_event_mock.return_value = mock_time_event

        expected_span_json = {
            'spanId': span_id,
            'parentSpanId': parent_span_id,
            'startTime': start_time,
            'endTime': end_time,
            'attributes': {
                'attributeMap': {
                    'component': {
                        'string_value': {
                            'truncated_byte_count': 0,
                            'value': 'HTTP load balancer'
                        }
                    },
                    'http.status_code': {
                        'string_value': {
                            'truncated_byte_count': 0,
                            'value': '200'
                        }
                    }
                }
            },
            'links': links,
            'stackTrace': mock_stack_trace,
            'status': mock_status,
            'timeEvents': {
                'timeEvent': [mock_time_event]
            },
            'displayName': {
                'truncated_byte_count': 0,
                'value': 'test span'
            },
            'childSpanCount': 0,
            'sameProcessAsParentSpan': True
        }

        span_json = format_span_json(span)

        print(span_json)

        print(expected_span_json)
        self.assertEqual(span_json, expected_span_json)
