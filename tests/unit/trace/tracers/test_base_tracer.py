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

from opencensus.trace.tracers import base


class TestBaseTracer(unittest.TestCase):
    def test_finish_abstract(self):
        tracer = base.Tracer()

        with self.assertRaises(NotImplementedError):
            tracer.finish()

    def test_span_abstract(self):
        tracer = base.Tracer()

        with self.assertRaises(NotImplementedError):
            tracer.span()

    def test_start_span_abstract(self):
        tracer = base.Tracer()

        with self.assertRaises(NotImplementedError):
            tracer.start_span()

    def test_end_span_abstract(self):
        tracer = base.Tracer()

        with self.assertRaises(NotImplementedError):
            tracer.end_span()

    def test_current_span_abstract(self):
        tracer = base.Tracer()

        with self.assertRaises(NotImplementedError):
            tracer.current_span()

    def test_add_attribute_to_current_span(self):
        tracer = base.Tracer()
        attribute_key = 'key'
        attribute_value = 'value'

        with self.assertRaises(NotImplementedError):
            tracer.add_attribute_to_current_span(attribute_key,
                                                 attribute_value)

    def test_list_collected_spans_abstract(self):
        tracer = base.Tracer()

        with self.assertRaises(NotImplementedError):
            tracer.list_collected_spans()
