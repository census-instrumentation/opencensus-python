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

from six.moves import queue
from opencensus.ext.azure.common import Options


class QueueEvent(object):
    def __init__(self, name):
        self.name = name
        self.event = threading.Event()

    def __repr__(self):
        return ('{}({})'.format(type(self).__name__, self.name))

    def set(self):
        return self.event.set()

    def wait(self, timeout=None):
        return self.event.wait(timeout)


class BaseExporter(object):
    EXIT_EVENT = QueueEvent('EXIT')

    def __init__(self, **options):
        self.options = Options(**options)
        self.grace_period = self.options.grace_period
        self.interval = self.options.export_interval
        self.max_batch_size = self.options.max_batch_size
        self._stopping = False
        self._queue = queue.Queue(maxsize=self.options.max_queue_size)
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
                if isinstance(item, QueueEvent):
                    return
            except queue.Empty:
                break
            cnt += 1
        while cnt < count:
            wait_time = max(timeout - elapsed_time, 0)
            try:
                item = self._queue.get(block=True, timeout=wait_time)
                yield item
                if isinstance(item, QueueEvent):
                    return
            except queue.Empty:
                break
            cnt += 1
            elapsed_time = time.time() - start_time

    def _gets(self, count, timeout):
        return tuple(self.__gets(count, timeout))

    def _stop(self, timeout=None):
        start_time = time.time()
        wait_time = timeout
        if self._thread.is_alive() and not self._stopping:
            self._stopping = True
            self._queue.put(self.EXIT_EVENT, block=True, timeout=wait_time)
            elapsed_time = time.time() - start_time
            wait_time = timeout and max(timeout - elapsed_time, 0)
        if self.EXIT_EVENT.wait(timeout=wait_time):
            return time.time() - start_time  # time taken to stop

    def _thread_entry(self):
        while True:
            batch = self._gets(self.max_batch_size, timeout=self.interval)
            if batch and isinstance(batch[-1], QueueEvent):
                self.emit(batch[:-1], event=batch[-1])
                if batch[-1] is self.EXIT_EVENT:
                    break
                else:
                    continue
            self.emit(batch)

    def emit(self, batch, event=None):
        raise NotImplementedError  # pragma: NO COVER

    def export(self, items):
        for item in items:
            try:
                self._queue.put(item, block=False)
            except queue.Full:
                pass  # TODO: log data loss

    def flush(self, timeout=None):
        start_time = time.time()
        wait_time = timeout
        event = QueueEvent('SYNC(timeout={})'.format(wait_time))
        try:
            self._queue.put(event, block=True, timeout=wait_time)
        except queue.Full:
            return
        elapsed_time = time.time() - start_time
        wait_time = timeout and max(timeout - elapsed_time, 0)
        if event.wait(timeout):
            return time.time() - start_time  # time taken to flush
