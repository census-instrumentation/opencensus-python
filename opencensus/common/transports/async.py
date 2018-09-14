# Copyright 2018, OpenCensus Authors
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
import logging
import threading
import time

from six.moves import queue
from six.moves import range

from opencensus.common.transports import base

_DEFAULT_GRACE_PERIOD = 5.0  # Seconds
_DEFAULT_MAX_BATCH_SIZE = 10
_WAIT_PERIOD = 1.0  # Seconds
_WORKER_THREAD_NAME = 'opencensus.common.Worker'
_WORKER_TERMINATOR = object()


class _Worker(object):
    """A background thread that exports batches of data.

    :type exporter: :class:`~opencensus.trace.exporters.base.Exporter` or
                    :class:`~opencensus.stats.exporters.base.StatsExporter`
    :param exporter: Instances of Exporter objects. Defaults to
                    :class:`.PrintExporter`. The rest options are
                    :class:`.ZipkinExporter`, :class:`.StackdriverExporter`,
                    :class:`.LoggingExporter`, :class:`.FileExporter`.

    :type grace_period: float
    :param grace_period: The amount of time to wait for pending data to
                         be submitted when the process is shutting down.

    :type max_batch_size: int
    :param max_batch_size: The maximum number of items to send at a time
                           in the background thread.
    """
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
        """Returns True is the background thread is running."""
        return self._thread is not None and self._thread.is_alive()

    def _get_items(self):
        """Get multiple items from a Queue.

        Gets at least one (blocking) and at most ``max_batch_size`` items
        (non-blocking) from a given Queue. Does not mark the items as done.

        :rtype: Sequence
        :returns: A sequence of items retrieved from the queue.
        """
        items = [self._queue.get()]

        while len(items) < self._max_batch_size:
            try:
                items.append(self._queue.get_nowait())
            except queue.Empty:
                break

        return items

    def _thread_main(self):
        """The entry point for the worker thread.

        Pulls pending data off the queue and writes them in
        batches to the specified tracing backend using the exporter.
        """
        quit_ = False

        while True:
            items = self._get_items()
            data = []

            for item in items:
                if item is _WORKER_TERMINATOR:
                    quit_ = True
                    # Continue processing items, don't break, try to process
                    # all items we got back before quitting.
                else:
                    data.extend(item)

            if data:
                try:
                    self.exporter.emit(data)
                except Exception:
                    logging.exception(
                        '%s failed to emit data.'
                        'Dropping %s objects from queue.',
                        self.exporter.__class__.__name__,
                        len(data))
                    pass

            for _ in range(len(items)):
                self._queue.task_done()

            # Wait for a while before next export
            time.sleep(_WAIT_PERIOD)

            if quit_:
                break

    def start(self):
        """Starts the background thread.

        Additionally, this registers a handler for process exit to attempt
        to send any pending data before shutdown.
        """
        with self._lock:
            if self.is_alive:
                return

            self._thread = threading.Thread(
                target=self._thread_main, name=_WORKER_THREAD_NAME)
            self._thread.daemon = True
            self._thread.start()
            atexit.register(self._export_pending_data)

    def stop(self):
        """Signals the background thread to stop.

        This does not terminate the background thread. It simply queues the
        stop signal. If the main process exits before the background thread
        processes the stop signal, it will be terminated without finishing
        work. The ``grace_period`` parameter will give the background
        thread some time to finish processing before this function returns.

        :rtype: bool
        :returns: True if the thread terminated. False if the thread is still
                  running.
        """
        if not self.is_alive:
            return True

        with self._lock:
            self._queue.put_nowait(_WORKER_TERMINATOR)
            self._thread.join(timeout=self._grace_period)

            success = not self.is_alive
            self._thread = None

            return success

    def _export_pending_data(self):
        """Callback that attempts to send pending data before termination."""
        if not self.is_alive:
            return
        self.stop()

    def enqueue(self, data):
        """Queues data to be written by the background thread."""
        self._queue.put_nowait(data)

    def flush(self):
        """Submit any pending data."""
        self._queue.join()


class AsyncTransport(base.Transport):
    """Asynchronous transport that uses a background thread.

    :type exporter: :class:`~opencensus.trace.exporters.base.Exporter` or
                    :class:`~opencensus.stats.exporters.base.StatsExporter`
    :param exporter: Instances of Exporter objects. Defaults to
                     :class:`.PrintExporter`. The rest options are
                     :class:`.ZipkinExporter`, :class:`.StackdriverExporter`,
                     :class:`.LoggingExporter`, :class:`.FileExporter`.

    :type grace_period: float
    :param grace_period: The amount of time to wait for pending data to
                         be submitted when the process is shutting down.

    :type max_batch_size: int
    :param max_batch_size: The maximum number of items to send at a time
                           in the background thread.
    """

    def __init__(self, exporter, grace_period=_DEFAULT_GRACE_PERIOD,
                 max_batch_size=_DEFAULT_MAX_BATCH_SIZE):
        self.exporter = exporter
        self.worker = _Worker(exporter, grace_period, max_batch_size)
        self.worker.start()

    def export(self, data):
        """Put the trace/stats to be exported into queue."""
        self.worker.enqueue(data)

    def flush(self):
        """Submit any pending traces/stats."""
        self.worker.flush()
