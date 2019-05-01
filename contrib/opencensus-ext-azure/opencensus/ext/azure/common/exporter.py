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

import atexit
import threading
import time

from six.moves.queue import Empty
from six.moves.queue import Queue


class BaseExporter(object):
    _EXIT_MESSAGE = object()

    def __init__(self, interval=15, max_batch_size=100, grace_period=5):
        self.grace_period = grace_period
        self.interval = interval
        self.max_batch_size = max_batch_size
        self._stopping = False
        self._queue = Queue(0)
        self._thread = threading.Thread(target=self._thread_entry)
        self._thread.daemon = True
        self._thread.start()
        atexit.register(self._stop, self.grace_period)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self._stop(None)

    def __gets(self, count, timeout):
        start_time = time.time()
        elapsed_time = 0
        cnt = 0
        while cnt < count:
            try:
                item = self._queue.get(block=False)
                yield item
                if item is self._EXIT_MESSAGE:
                    return
            except Empty:
                break
            cnt += 1
        while cnt < count:
            wait_time = max(timeout - elapsed_time, 0)
            try:
                item = self._queue.get(block=True, timeout=wait_time)
                yield item
                if item is self._EXIT_MESSAGE:
                    return
            except Empty:
                break
            cnt += 1
            elapsed_time = time.time() - start_time

    def _gets(self, count, timeout):
        return tuple(self.__gets(count, timeout))

    def _stop(self, timeout):
        start_time = time.time()
        wait_time = timeout
        if not self._stopping:
            self._stopping = True
            self._queue.put(self._EXIT_MESSAGE, block=True, timeout=wait_time)
            elapsed_time = time.time() - start_time
            wait_time = timeout and max(timeout - elapsed_time, 0)
        self._thread.join(timeout=wait_time)

    def _thread_entry(self):
        while True:
            batch = self._gets(self.max_batch_size, self.interval)
            if batch and batch[-1] is self._EXIT_MESSAGE:
                self.emit(batch[:-1], last_batch=True)
                break
            self.emit(batch)

    def emit(self, batch, last_batch=False):
        raise NotImplementedError  # pragma: NO COVER
