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


class QueueExitEvent(QueueEvent):
    pass


class Queue(queue.Queue):
    CAPACITY = 8192  # TODO: make it configurable

    def __init__(self):
        self.EXIT_EVENT = QueueExitEvent('EXIT')
        self._queue = queue.Queue(maxsize=self.CAPACITY)

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
        self._queue.put(item, block, timeout)


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


class BaseExporter(object):
    def __init__(self, **options):
        options = Options(**options)
        self.export_interval = options.export_interval
        self.max_batch_size = options.max_batch_size
        # TODO: queue should be moved to tracer
        # too much refactor work, leave to the next PR
        self._queue = Queue()
        self.EXIT_EVENT = self._queue.EXIT_EVENT
        # TODO: worker should not be created in the base exporter
        self._worker = Worker(self._queue, self)
        self._worker.start()
        atexit.register(self._worker.stop, options.grace_period)

    # Ideally we don't want to have emit and export
    # Exporter will have three APIs:
    # 1) on_span_begin (run synchronously, similar like IRQ)
    # 2) on_span_end (run synchronously, similar like IRQ)
    # 3) export (run asynchronously in the worker thread, like DPC)
    # IRQ should do as less as possible, capture all the required context information
    # All the context insensitive processing (e.g. format time string, serialization,
    # validation, networking operation, file operation) should be deferred to DPC.
    # The exporter can optionally provide the 4th API, transmit(data), which can be
    # used to transmit the data synchronously and return the status to the caller.
    # This could be useful for auditing scenario.
    # One possible way of consuming the API is:
    # def on_span_end(self, span, span_data):
    #     payload = transform(span_data)
    #     self.transmit(payload)
    def emit(self, batch, event=None):
        raise NotImplementedError  # pragma: NO COVER

    # TODO: we shouldn't have this at the beginning
    # Tracer should own the queue, exporter shouldn't even know if the source is a queue or not
    # Tracer puts span_data into the queue
    # Worker gets span_data from the src (here is the queue) and feed into the dst (exporter)
    # Exporter defines the MTU (max_batch_size) and exporter_interval
    # There can be one worker for each queue, or multiple workers for each queue, or
    # shared workers among queues (e.g. queue for traces, queue for logs)
    def export(self, items):
        for item in items:
            try:
                self._queue.put(item, block=False)
            except queue.Full:
                pass  # TODO: log data loss
