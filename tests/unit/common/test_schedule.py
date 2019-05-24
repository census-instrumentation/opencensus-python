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

from opencensus.common.schedule import PeriodicTask
from opencensus.common.schedule import Queue
from opencensus.common.schedule import QueueEvent

TIMEOUT = .1


class TestQueueEvent(unittest.TestCase):
    def test_basic(self):
        evt = QueueEvent('foobar')
        self.assertFalse(evt.wait(timeout=TIMEOUT))
        evt.set()
        self.assertTrue(evt.wait(timeout=TIMEOUT))


class TestQueue(unittest.TestCase):
    def test_gets(self):
        queue = Queue(capacity=10)
        queue.puts((1, 2, 3))
        result = queue.gets(count=5, timeout=TIMEOUT)
        self.assertEqual(result, (1, 2, 3))

        queue.puts((1, 2, 3, 4, 5))
        result = queue.gets(count=3, timeout=TIMEOUT)
        self.assertEqual(result, (1, 2, 3))
        result = queue.gets(count=3, timeout=TIMEOUT)
        self.assertEqual(result, (4, 5))

    def test_gets_event(self):
        queue = Queue(capacity=10)
        event = QueueEvent('test')
        queue.puts((event, 1, 2, 3, event))
        result = queue.gets(count=5, timeout=TIMEOUT)
        self.assertEqual(result, (event,))
        result = queue.gets(count=5, timeout=TIMEOUT)
        self.assertEqual(result, (1, 2, 3, event))

        task = PeriodicTask(TIMEOUT / 10, lambda: queue.put(1))
        task.start()
        try:
            result = queue.gets(count=5, timeout=TIMEOUT)
            self.assertEqual(result, (1, 1, 1, 1, 1))
        finally:
            task.cancel()
            task.join()

    def test_flush_timeout(self):
        queue = Queue(capacity=10)
        self.assertEqual(queue.flush(timeout=TIMEOUT), 0)
        queue.put('test', timeout=TIMEOUT)
        self.assertIsNone(queue.flush(timeout=TIMEOUT))
        queue.puts(range(100), timeout=TIMEOUT)
        self.assertIsNone(queue.flush(timeout=TIMEOUT))

        def proc():
            for item in queue.gets(count=1, timeout=TIMEOUT):
                if isinstance(item, QueueEvent):
                    item.set()

        task = PeriodicTask(TIMEOUT / 10, proc)
        task.start()
        try:
            self.assertIsNotNone(queue.flush())
        finally:
            task.cancel()
            task.join()

    def test_puts_timeout(self):
        queue = Queue(capacity=10)
        queue.puts(range(100), timeout=TIMEOUT)
