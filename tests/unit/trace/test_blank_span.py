import unittest

import mock

import datetime
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

        time_event = TimeEvent(datetime.datetime.now())
        span.add_time_event(time_event)

        span_iter_list = list(iter(span))
        self.assertEqual(span_iter_list, [span])

        expected_span_json = {
            'spanId': 'test_span_id',
            'startTime': None,
            'endTime': None,
            'displayName': {
                'truncated_byte_count': 0,
                'value': 'test_span_name'},
            'childSpanCount': 0,
        }
        span_json = format_span_json(span)
        self.assertEqual(span_json, expected_span_json)

        span.start()
        span.finish()
