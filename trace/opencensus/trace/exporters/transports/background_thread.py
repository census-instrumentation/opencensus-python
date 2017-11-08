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

import atexit
import threading
import time

from six.moves import queue
from six.moves import range

_DEFAULT_GRACE_PERIOD = 5.0  # Seconds
_WAIT_PERIOD = 3.0  # Seconds
_DEFAULT_MAX_BATCH_SIZE = 2
_WORKER_THREAD_NAME = 'opencensus.trace.Worker'
_WORKER_TERMINATOR = object()


class _Worker(object):
    def __init__(self, exporter, grace_period=_DEFAULT_GRACE_PERIOD,
                 max_batch_size=_DEFAULT_MAX_BATCH_SIZE):
        self.exporter = exporter
        self._grace_period = grace_period
        self._max_batch_size = max_batch_size
        self._queue = queue.Queue(0)
        self._lock = threading.Lock()
        self._thread = None

    @property
    def is_alive(self):
        return self._thread is not None and self._thread.is_alive()

    def _get_items(self):
        items = [self._queue.get()]

        while len(items) < self._max_batch_size:
            try:
                items.append(self._queue.get_nowait())
            except queue.Empty:
                break

        return items

    def _thread_main(self):
        print('Background thread started.')

        quit_ = False

        while True:
            items = self._get_items()
            trace_id = None
            spans = []

            if items[0] is not _WORKER_TERMINATOR:
                trace_id = items[0].get('traceId')

            for item in items:
                if item is _WORKER_TERMINATOR:
                    quit_ = True
                else:
                    spans.extend(item.get('spans'))

            if spans and trace_id:
                spans_json = {
                    'traceId': trace_id,
                    'spans': spans,
                }
                self.exporter.emit(spans_json)

            for _ in range(len(items)):
                self._queue.task_done()

            # Wait for a while before next export
            time.sleep(_WAIT_PERIOD)

            if quit_:
                break

        print('Background thread exited.')

    def start(self):
        # Ensure calling start again does not create a new thread
        with self._lock:
            if self.is_alive:
                return

            self._thread = threading.Thread(
                target=self._thread_main, name=_WORKER_THREAD_NAME)
            self._thread.daemon = True
            self._thread.start()
            atexit.register(self._export_pending_spans)

    def stop(self):
        if not self.is_alive:
            return True

        with self._lock:
            self._queue.put_nowait(_WORKER_TERMINATOR)
            self._thread.join(timeout=self._grace_period)

            success = not self.is_alive
            self._thread = None

            return success

    def _export_pending_spans(self):
        if not self.is_alive:
            return

        if not self._queue.empty():
            print('Sending all pending spans before terminated.')

        if self.stop():
            print('Sent all pending spans.')
        else:
            print('Failed to send pending spans.')

    def enqueue(self, trace):
        self._queue.put_nowait(trace)

    def flush(self):
        self._queue.join()


class BackgroundThreadTransport(object):
    def __init__(self, exporter, grace_period=_DEFAULT_GRACE_PERIOD,
                 max_batch_size=_DEFAULT_MAX_BATCH_SIZE):
        self.exporter = exporter
        self.worker = _Worker(exporter, grace_period, max_batch_size)
        self.worker.start()

    def export(self, trace):
        self.worker.enqueue(trace)

    def flush(self):
        self.worker.flush()
