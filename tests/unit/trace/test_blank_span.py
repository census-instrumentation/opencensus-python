# Copyright 2018, OpenCensus Authors
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
import mock
import unittest

from opencensus.common import utils
from opencensus.trace.link import Link
from opencensus.trace.span import format_span_json
from opencensus.trace.time_event import TimeEvent


class TestBlankSpan(unittest.TestCase):
    @staticmethod
    def _get_target_class():
        from opencensus.trace.blank_span import BlankSpan

        return BlankSpan

    def _make_one(self, *args, **kw):
        return self._get_target_class()(*args, **kw)

    def test_do_not_crash(self):
        span_id = 'test_span_id'
        span_name = 'test_span_name'

        patch = mock.patch(
            'opencensus.trace.blank_span.generate_span_id',
            return_value=span_id)

        with patch:
            span = self._make_one(span_name)

        self.assertEqual(span.name, span_name)
        self.assertEqual(span.span_id, span_id)
        self.assertIsNotNone(span.parent_span)
        self.assertIsNotNone(span.parent_span.span())
        self.assertEqual(span.attributes, {})
        self.assertIsNone(span.start_time)
        self.assertIsNone(span.end_time)
        self.assertEqual(span.children, [])
        self.assertIsNone(span.context_tracer)

        span.add_attribute('attribute_key', 'attribute_value')
        span.add_annotation('This is a test', name='blank-span')

        link = Link(span_id='1234', trace_id='4567')
        span.add_link(link)

        time_event = mock.Mock()

        with self.assertRaises(TypeError):
            span.add_time_event(time_event)

        time_event = TimeEvent(datetime.datetime.utcnow())
        span.add_time_event(time_event)

        span_iter_list = list(iter(span))
        self.assertEqual(span_iter_list, [span])

        expected_span_json = {
            'spanId': 'test_span_id',
            'startTime': None,
            'endTime': None,
            'displayName': {
                'truncated_byte_count': 0,
                'value': 'test_span_name'
            },
            'childSpanCount': 0,
        }
        span_json = format_span_json(span)
        self.assertEqual(span_json, expected_span_json)

        span.start()
        span.finish()

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
        self.assertIsNotNone(span.span_id)
        self.assertEqual(span.attributes, {})
        self.assertEqual(span.start_time, start_time)
        self.assertEqual(span.end_time, end_time)
        self.assertEqual(span.time_events, time_events)
        self.assertEqual(span.stack_trace, stack_trace)
        self.assertEqual(span.links, [])
        self.assertEqual(span.status, status)
        self.assertEqual(span.children, [])
        self.assertEqual(span.context_tracer, context_tracer)

    def test_start(self):
        span_name = 'root_span'
        span = self._make_one(span_name)
        self.assertIsNone(span.start_time)

        span.start()
        self.assertIsNone(span.start_time)

    def test_finish_without_context_tracer(self):
        span_name = 'root_span'
        span = self._make_one(span_name)
        self.assertIsNone(span.end_time)

        span.finish()
        self.assertIsNone(span.end_time)

    def test_finish(self):
        span_name = 'root_span'
        span = self._make_one(span_name)
        self.assertIsNone(span.end_time)

        span.finish()
        self.assertIsNone(span.end_time)

    def test_on_create(self):
        from opencensus.trace.blank_span import BlankSpan
        self.on_create_called = False
        self._make_one('span1')
        self.assertFalse(self.on_create_called)
        try:

            @BlankSpan.on_create
            def callback(span):
                self.on_create_called = True

            self._make_one('span2')
        finally:
            BlankSpan._on_create_callbacks = []
        self.assertFalse(self.on_create_called)

    def test_context_manager(self):
        span_name = 'root_span'
        with self._make_one(span_name) as s:
            self.assertIsNotNone(s)
            self.assertEquals(s.name, span_name)
