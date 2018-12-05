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

from opencensus.trace import link as link_module


class TestLink(unittest.TestCase):
    def test_constructor_default(self):
        trace_id = 'test trace id'
        span_id = 'test span id'
        type = link_module.Type.TYPE_UNSPECIFIED
        attributes = mock.Mock()

        link = link_module.Link(
            trace_id=trace_id, span_id=span_id, attributes=attributes)

        self.assertEqual(link.trace_id, trace_id)
        self.assertEqual(link.span_id, span_id)
        self.assertEqual(link.type, type)
        self.assertEqual(link.attributes, attributes)

    def test_constructor_explicit(self):
        trace_id = 'test trace id'
        span_id = 'test span id'
        type = link_module.Type.CHILD_LINKED_SPAN
        attributes = mock.Mock()

        link = link_module.Link(
            trace_id=trace_id,
            span_id=span_id,
            type=type,
            attributes=attributes)

        self.assertEqual(link.trace_id, trace_id)
        self.assertEqual(link.span_id, span_id)
        self.assertEqual(link.type, type)
        self.assertEqual(link.attributes, attributes)

    def test_format_link_json_with_attributes(self):
        trace_id = 'test trace id'
        span_id = 'test span id'
        type = link_module.Type.CHILD_LINKED_SPAN
        attributes = mock.Mock()

        link = link_module.Link(
            trace_id=trace_id,
            span_id=span_id,
            type=type,
            attributes=attributes)

        link_json = link.format_link_json()

        expected_link_json = {
            'trace_id': trace_id,
            'span_id': span_id,
            'type': type,
            'attributes': attributes
        }

        self.assertEqual(expected_link_json, link_json)

    def test_format_link_json_without_attributes(self):
        trace_id = 'test trace id'
        span_id = 'test span id'
        type = link_module.Type.CHILD_LINKED_SPAN

        link = link_module.Link(trace_id=trace_id, span_id=span_id, type=type)

        link_json = link.format_link_json()

        expected_link_json = {
            'trace_id': trace_id,
            'span_id': span_id,
            'type': type
        }

        self.assertEqual(expected_link_json, link_json)
