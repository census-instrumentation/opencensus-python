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

import threading
import time

from six.moves import queue


class PeriodicTask(threading.Thread):
    """Thread that periodically calls a given function.

    :type interval: int or float
    :param interval: Seconds between calls to the function.

    :type function: function
    :param function: The function to call.

    :type args: list
    :param args: The args passed in while calling `function`.

    :type kwargs: dict
    :param args: The kwargs passed in while calling `function`.
    """

    def __init__(self, interval, function, args=None, kwargs=None):
        super(PeriodicTask, self).__init__()
        self.interval = interval
        self.function = function
        self.args = args or []
        self.kwargs = kwargs or {}
        self.finished = threading.Event()

    def run(self):
        wait_time = self.interval
        while not self.finished.wait(wait_time):
            start_time = time.time()
            self.function(*self.args, **self.kwargs)
            elapsed_time = time.time() - start_time
            wait_time = max(self.interval - elapsed_time, 0)

    def cancel(self):
        self.finished.set()


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


class QueueExitEvent(QueueEvent):
    pass


class Queue(queue.Queue):
    def __init__(self, capacity):
        self.EXIT_EVENT = QueueExitEvent('EXIT')
        self._queue = queue.Queue(maxsize=capacity)

    def _gets(self, count, timeout):
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

    def gets(self, count, timeout):
        return tuple(self._gets(count, timeout))

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

    def put(self, item, block=True, timeout=None):
        try:
            self._queue.put(item, block, timeout)
        except queue.Full:
            pass  # TODO: log data loss

    def puts(self, items, block=True, timeout=None):
        if block and timeout is not None:
            start_time = time.time()
            elapsed_time = 0
            for item in items:
                wait_time = max(timeout - elapsed_time, 0)
                self.put(item, block=True, timeout=wait_time)
                elapsed_time = time.time() - start_time
        else:
            for item in items:
                self.put(item, block, timeout)


class Worker(threading.Thread):
    daemon = True

    def __init__(self, src, dst):
        self.src = src
        self.dst = dst
        self._stopping = False
        super(Worker, self).__init__()

    def run(self):
        src = self.src
        dst = self.dst
        while True:
            batch = src.gets(dst.max_batch_size, dst.export_interval)
            if batch and isinstance(batch[-1], QueueEvent):
                dst.emit(batch[:-1], event=batch[-1])
                if batch[-1] is src.EXIT_EVENT:
                    break
                else:
                    continue
            dst.emit(batch)

    def stop(self, timeout=None):
        start_time = time.time()
        wait_time = timeout
        if self.is_alive() and not self._stopping:
            self._stopping = True
            self.src.put(self.src.EXIT_EVENT, block=True, timeout=wait_time)
            elapsed_time = time.time() - start_time
            wait_time = timeout and max(timeout - elapsed_time, 0)
        if self.src.EXIT_EVENT.wait(timeout=wait_time):
            return time.time() - start_time  # time taken to stop
