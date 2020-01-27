# Copyright 2019, OpenCensus Authors
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

from opencensus.ext.azure.common.processor import ProcessorMixin


# pylint: disable=W0212
class TestProcessorMixin(unittest.TestCase):
    def test_add(self):
        mixin = ProcessorMixin()
        mixin._telemetry_processors = []
        mixin.add_telemetry_processor(lambda: True)
        self.assertEqual(len(mixin._telemetry_processors), 1)

    def test_clear(self):
        mixin = ProcessorMixin()
        mixin._telemetry_processors = []
        mixin.add_telemetry_processor(lambda: True)
        self.assertEqual(len(mixin._telemetry_processors), 1)
        mixin.clear_telemetry_processors()
        self.assertEqual(len(mixin._telemetry_processors), 0)

    def test_apply(self):
        mixin = ProcessorMixin()
        mixin._telemetry_processors = []
        def call_back_function(envelope):
            envelope.append('hello')
        mixin.add_telemetry_processor(call_back_function)
        envelope = ['add', 'sub']
        mixin.apply_telemetry_processors([envelope])
        self.assertEqual(len(envelope), 3)
        self.assertEqual(envelope[0], 'add')
        self.assertEqual(envelope[1], 'sub')
        self.assertEqual(envelope[2], 'hello')

    def test_apply_multiple(self):
        mixin = ProcessorMixin()
        mixin._telemetry_processors = []
        def call_back_function(envelope):
            envelope.append('hello')
        def call_back_function2(envelope):
            envelope.append('hello2')
        mixin.add_telemetry_processor(call_back_function)
        mixin.add_telemetry_processor(call_back_function2)
        envelope = ['add']
        mixin.apply_telemetry_processors([envelope])
        self.assertEqual(len(envelope), 3)
        self.assertEqual(envelope[0], 'add')
        self.assertEqual(envelope[1], 'hello')
        self.assertEqual(envelope[2], 'hello2')

    def test_apply_exception(self):
        mixin = ProcessorMixin()
        mixin._telemetry_processors = []
        def call_back_function(envelope):
            raise ValueError()
        def call_back_function2(envelope):
            envelope.append('hello2')
        mixin.add_telemetry_processor(call_back_function)
        mixin.add_telemetry_processor(call_back_function2)
        envelope = ['add']
        mixin.apply_telemetry_processors([envelope])
        self.assertEqual(len(envelope), 2)
        self.assertEqual(envelope[0], 'add')
        self.assertEqual(envelope[1], 'hello2')
