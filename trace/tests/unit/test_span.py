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


class TestSpan(unittest.TestCase):

    project = 'PROJECT'

    @staticmethod
    def _get_target_class():
        from opencensus.trace.span import Span

        return Span

    def _make_one(self, *args, **kw):
        return self._get_target_class()(*args, **kw)

    def test_constructor_defaults(self):
        from opencensus.trace.enums import Enum

        span_id = 'test_span_id'
        span_name = 'test_span_name'

        patch = mock.patch(
            'opencensus.trace.span.generate_span_id',
            return_value=span_id)

        with patch:
            span = self._make_one(span_name)

        self.assertEqual(span.name, span_name)
        self.assertEqual(span.span_id, span_id)
        self.assertEqual(span.kind, Enum.SpanKind.SPAN_KIND_UNSPECIFIED)
        self.assertIsNone(span.parent_span)
        self.assertEqual(span.labels, {})
        self.assertIsNone(span.start_time)
        self.assertIsNone(span.end_time)
        self.assertEqual(span.children, [])
        self.assertIsNone(span.context_tracer)

    def test_constructor_explicit(self):
        from datetime import datetime

        from opencensus.trace.enums import Enum

        span_id = 'test_span_id'
        span_name = 'test_span_name'
        kind = Enum.SpanKind.RPC_CLIENT
        parent_span = mock.Mock()
        start_time = datetime.utcnow().isoformat() + 'Z'
        end_time = datetime.utcnow().isoformat() + 'Z'
        labels = {
            '/http/status_code': '200',
            '/component': 'HTTP load balancer',
        }
        context_tracer = mock.Mock()

        span = self._make_one(
            name=span_name,
            kind=kind,
            parent_span=parent_span,
            labels=labels,
            start_time=start_time,
            end_time=end_time,
            span_id=span_id,
            context_tracer=context_tracer)

        self.assertEqual(span.name, span_name)
        self.assertEqual(span.span_id, span_id)
        self.assertEqual(span.kind, kind)
        self.assertEqual(span.parent_span, parent_span)
        self.assertEqual(span.labels, labels)
        self.assertEqual(span.start_time, start_time)
        self.assertEqual(span.end_time, end_time)
        self.assertEqual(span.children, [])
        self.assertEqual(span.context_tracer, context_tracer)

    def test_span(self):
        from opencensus.trace.enums import Enum

        span_id = 'test_span_id'
        root_span_name = 'root_span'
        child_span_name = 'child_span'
        root_span = self._make_one(root_span_name)
        root_span._child_spans = []
        kind = Enum.SpanKind.SPAN_KIND_UNSPECIFIED

        patch = mock.patch(
            'opencensus.trace.span.generate_span_id',
            return_value=span_id)

        with patch:
            with root_span:
                root_span.span(child_span_name)

        self.assertEqual(len(root_span._child_spans), 1)

        result_child_span = root_span._child_spans[0]

        self.assertEqual(result_child_span.name, child_span_name)
        self.assertEqual(result_child_span.span_id, span_id)
        self.assertEqual(result_child_span.kind, kind)
        self.assertEqual(result_child_span.parent_span, root_span)
        self.assertEqual(result_child_span.labels, {})
        self.assertIsNone(result_child_span.start_time)
        self.assertIsNone(result_child_span.end_time)

    def test_add_label(self):
        span_name = 'test_span_name'
        span = self._make_one(span_name)
        label_key = 'label_key'
        label_value = 'label_value'
        span.add_label(label_key, label_value)

        self.assertEqual(span.labels[label_key], label_value)
        span.labels.pop(label_key, None)

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


class Test_format_span_json(unittest.TestCase):

    def test_format_span_json_no_parent_span(self):
        from opencensus.trace.span import format_span_json
        from opencensus.trace.enums import Enum

        name = 'test span'
        kind = Enum.SpanKind.SPAN_KIND_UNSPECIFIED
        span_id = 1234
        start_time = '2017-06-25'
        end_time = '2017-06-26'

        span = mock.Mock()
        span.name = name
        span.kind = kind
        span.span_id = span_id
        span.start_time = start_time
        span.end_time = end_time
        span.parent_span = None
        span.labels = None

        expected_span_json = {
            'name': name,
            'kind': kind,
            'spanId': span_id,
            'startTime': start_time,
            'endTime': end_time,
        }

        span_json = format_span_json(span)
        self.assertEqual(span_json, expected_span_json)

    def test_format_span_json_with_parent_span(self):
        from opencensus.trace.span import format_span_json
        from opencensus.trace.enums import Enum

        name = 'test span'
        kind = Enum.SpanKind.SPAN_KIND_UNSPECIFIED
        span_id = 1234
        labels = {
            '/http/status_code': '200',
            '/component': 'HTTP load balancer',
        }
        start_time = '2017-06-25'
        end_time = '2017-06-26'
        parent_span = mock.Mock()
        parent_span_id = 5678
        parent_span.span_id = parent_span_id

        span = mock.Mock()
        span.parent_span = parent_span
        span.name = name
        span.kind = kind
        span.labels = labels
        span.span_id = span_id
        span.start_time = start_time
        span.end_time = end_time

        expected_span_json = {
            'name': name,
            'kind': kind,
            'spanId': span_id,
            'parentSpanId': parent_span_id,
            'startTime': start_time,
            'endTime': end_time,
            'labels': labels,
        }

        span_json = format_span_json(span)
        self.assertEqual(span_json, expected_span_json)
