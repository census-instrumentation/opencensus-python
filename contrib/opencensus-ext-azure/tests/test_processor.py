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
from opencensus.ext.azure.common.protocol import Envelope


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

        def callback_function(envelope):
            envelope.baseType += '_world'
        mixin.add_telemetry_processor(callback_function)
        envelope = Envelope()
        envelope.baseType = 'type1'
        mixin.apply_telemetry_processors([envelope])
        self.assertEqual(envelope.baseType, 'type1_world')

    def test_apply_multiple(self):
        mixin = ProcessorMixin()
        mixin._telemetry_processors = []

        def callback_function(envelope):
            envelope.baseType += '_world'

        def callback_function2(envelope):
            envelope.baseType += '_world2'
        mixin.add_telemetry_processor(callback_function)
        mixin.add_telemetry_processor(callback_function2)
        envelope = Envelope()
        envelope.baseType = 'type1'
        mixin.apply_telemetry_processors([envelope])
        self.assertEqual(envelope.baseType, 'type1_world_world2')

    def test_apply_exception(self):
        mixin = ProcessorMixin()
        mixin._telemetry_processors = []

        def callback_function(envelope):
            raise ValueError()

        def callback_function2(envelope):
            envelope.baseType += '_world2'
        mixin.add_telemetry_processor(callback_function)
        mixin.add_telemetry_processor(callback_function2)
        envelope = Envelope()
        envelope.baseType = 'type1'
        mixin.apply_telemetry_processors([envelope])
        self.assertEqual(envelope.baseType, 'type1_world2')

    def test_apply_not_accepted(self):
        mixin = ProcessorMixin()
        mixin._telemetry_processors = []

        def callback_function(envelope):
            return envelope.baseType == 'type2'
        mixin.add_telemetry_processor(callback_function)
        envelope = Envelope()
        envelope.baseType = 'type1'
        envelope2 = Envelope()
        envelope2.baseType = 'type2'
        envelopes = mixin.apply_telemetry_processors([envelope, envelope2])
        self.assertEqual(len(envelopes), 1)
        self.assertEqual(envelopes[0].baseType, 'type2')
