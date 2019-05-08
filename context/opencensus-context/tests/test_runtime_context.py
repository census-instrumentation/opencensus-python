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
from opencensus.common.runtime_context import RuntimeContext


class RuntimeContextTest(unittest.TestCase):
    def test_register(self):
        RuntimeContext.register_slot('foo')
        self.assertIsNone(RuntimeContext.foo)

        RuntimeContext.foo = 123
        self.assertEqual(RuntimeContext.foo, 123)

    def test_register_with_default(self):
        RuntimeContext.register_slot('bar', 123)
        self.assertEqual(RuntimeContext.bar, 123)

    def test_register_duplicate(self):
        self.assertRaises(ValueError, lambda: [
            RuntimeContext.register_slot('dup'),
            RuntimeContext.register_slot('dup'),
        ])

    def test_get_non_existing(self):
        self.assertRaises(AttributeError, lambda: RuntimeContext.non_existing)

    def test_set_non_existing(self):
        def set_non_existing():
            RuntimeContext.non_existing = 1

        self.assertRaises(AttributeError, set_non_existing)

    def test_clear(self):
        RuntimeContext.register_slot('baz')
        RuntimeContext.baz = 123
        self.assertEqual(RuntimeContext.baz, 123)
        RuntimeContext.clear()
        self.assertEqual(RuntimeContext.baz, None)

    def test_with_current_context(self):
        from threading import Thread

        RuntimeContext.register_slot('operation_id')

        def work(name):
            self.assertEqual(RuntimeContext.operation_id, 'foo')
            RuntimeContext.operation_id = name
            self.assertEqual(RuntimeContext.operation_id, name)

        RuntimeContext.operation_id = 'foo'
        thread = Thread(
            target=RuntimeContext.with_current_context(work),
            args=('bar'),
        )
        thread.start()
        thread.join()

        self.assertEqual(RuntimeContext.operation_id, 'foo')
