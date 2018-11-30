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

from opencensus.trace import trace_options as trace_opt


class TestTraceOptions(unittest.TestCase):
    def test_constructor_default(self):
        trace_options = trace_opt.TraceOptions()

        self.assertEqual(trace_options.trace_options_byte, trace_opt.DEFAULT)
        self.assertTrue(trace_options.enabled)

    def test_constructor_explicit(self):
        trace_options_byte = '0'
        trace_options = trace_opt.TraceOptions(trace_options_byte)

        self.assertEqual(trace_options.trace_options_byte, trace_options_byte)
        self.assertFalse(trace_options.enabled)

    def test_check_trace_options_valid(self):
        trace_options_byte = '10'
        trace_options = trace_opt.TraceOptions(trace_options_byte)

        self.assertEqual(trace_options.trace_options_byte, trace_options_byte)

    def test_check_trace_options_invalid(self):
        trace_options_byte = '256'
        trace_options = trace_opt.TraceOptions(trace_options_byte)

        self.assertEqual(trace_options.trace_options_byte, trace_opt.DEFAULT)
