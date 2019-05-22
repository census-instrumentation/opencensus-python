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
import logging
import json
import requests
import threading
import time

from opencensus.common.schedule import Queue
from opencensus.common.schedule import QueueEvent
from opencensus.ext.azure.common import Options
from opencensus.ext.azure.common import utils

logger = logging.getLogger(__name__)

__all__ = ['AzureExporter', 'LogHandler']


class AzureExporter(object):
    """An exporter that sends logs to Microsoft Azure Monitor.

    :type options: dict
    :param options: Options for the exporter. Defaults to None.
    """

    def __init__(self, **options):
        self.options = Options(**options)
        if not self.options.instrumentation_key:
            raise ValueError('The instrumentation_key is not provided.')
        self.export_interval = self.options.export_interval
        self.max_batch_size = self.options.max_batch_size

    def export(self, batch, event=None):
        if batch:
            for item in batch:
                trace_id = getattr(item, 'traceId', 'N/A')
                span_id = getattr(item, 'spanId', 'N/A')
                print('{levelname} {trace_id} {span_id} {pathname}:L{lineno} {msg}'.format(trace_id=trace_id, span_id=span_id, **vars(item)))
        if event:
            event.set()


class LogHandler(logging.Handler):
    def __init__(self, exporter):
        logging.Handler.__init__(self)
        self.exporter = exporter
        self._queue = Queue(capacity=8192)  # TODO: make this configurable
        self._worker = Worker(self._queue, self.exporter)
        self._worker.start()

    def close(self):
        self._worker.stop()

    def createLock(self):
        self.lock = None

    def emit(self, record):
        self._queue.put(record, block=False)

    def flush(self, timeout=None):
        self._queue.flush(timeout=timeout)


class Worker(threading.Thread):
    daemon = True

    def __init__(self, src, dst):
        self.src = src
        self.dst = dst
        self._stopping = False
        super(Worker, self).__init__()

    def run(self):  # pragma: NO COVER
        src = self.src
        dst = self.dst
        while True:
            batch = src.gets(dst.max_batch_size, dst.export_interval)
            if batch and isinstance(batch[-1], QueueEvent):
                dst.export(batch[:-1], event=batch[-1])
                if batch[-1] is src.EXIT_EVENT:
                    break
                else:
                    continue
            dst.export(batch)

    def stop(self, timeout=None):  # pragma: NO COVER
        start_time = time.time()
        wait_time = timeout
        if self.is_alive() and not self._stopping:
            self._stopping = True
            self.src.put(self.src.EXIT_EVENT, block=True, timeout=wait_time)
            elapsed_time = time.time() - start_time
            wait_time = timeout and max(timeout - elapsed_time, 0)
        if self.src.EXIT_EVENT.wait(timeout=wait_time):
            return time.time() - start_time  # time taken to stop
