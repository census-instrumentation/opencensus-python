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
        queue = Queue(capacity=100)
        queue.puts((1, 2, 3))
        result = queue.gets(count=5, timeout=TIMEOUT)
        self.assertEquals(result, (1, 2, 3))

        queue.puts((1, 2, 3, 4, 5))
        result = queue.gets(count=5, timeout=0)
        self.assertEquals(result, (1, 2, 3, 4, 5))
