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

from opencensus.common import utils
from opencensus.trace import link
from opencensus.trace import span_context
from opencensus.trace import span_data as span_data_module
from opencensus.trace import stack_trace
from opencensus.trace import status
from opencensus.trace import time_event


class TestSpanData(unittest.TestCase):
    def test_create_span_data(self):
        span_data_module.SpanData(
            name='root',
            context=None,
            span_id='6e0c63257de34c92',
            parent_span_id='6e0c63257de34c93',
            attributes={'key1': 'value1'},
            start_time=utils.to_iso_str(),
            end_time=utils.to_iso_str(),
            stack_trace=None,
            links=None,
            status=None,
            time_events=None,
            same_process_as_parent_span=None,
            child_span_count=None,
            span_kind=0,
        )

    def test_span_data_immutable(self):
        span_data = span_data_module.SpanData(
            name='root',
            context=None,
            span_id='6e0c63257de34c92',
            parent_span_id='6e0c63257de34c93',
            attributes={'key1': 'value1'},
            start_time=utils.to_iso_str(),
            end_time=utils.to_iso_str(),
            stack_trace=None,
            links=None,
            status=None,
            time_events=None,
            same_process_as_parent_span=None,
            child_span_count=None,
            span_kind=0,
        )
        with self.assertRaises(AttributeError):
            span_data.name = 'child'

        with self.assertRaises(AttributeError):
            span_data.new_attr = 'a'

    def test_format_legacy_trace_json(self):
        trace_id = '2dd43a1d6b2549c6bc2a1a54c2fc0b05'
        span_data = span_data_module.SpanData(
            name='root',
            context=span_context.SpanContext(
                trace_id=trace_id,
                span_id='6e0c63257de34c92'
            ),
            span_id='6e0c63257de34c92',
            parent_span_id='6e0c63257de34c93',
            attributes={'key1': 'value1'},
            start_time=utils.to_iso_str(),
            end_time=utils.to_iso_str(),
            stack_trace=stack_trace.StackTrace(stack_trace_hash_id='111'),
            links=[link.Link('1111', span_id='6e0c63257de34c92')],
            status=status.Status(code=0, message='pok'),
            time_events=[
                time_event.TimeEvent(
                    timestamp=datetime.datetime(1970, 1, 1)
                )
            ],
            same_process_as_parent_span=False,
            child_span_count=0,
            span_kind=0,
        )
        trace_json = span_data_module.format_legacy_trace_json([span_data])
        self.assertEqual(trace_json.get('traceId'), trace_id)
        self.assertEqual(len(trace_json.get('spans')), 1)
