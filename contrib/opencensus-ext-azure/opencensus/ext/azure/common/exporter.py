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

from opencensus.common.schedule import Queue
from opencensus.common.schedule import Worker
from opencensus.ext.azure.common import Options


class BaseExporter(object):
    def __init__(self, **options):
        options = Options(**options)
        self.export_interval = options.export_interval
        self.max_batch_size = options.max_batch_size
        # TODO: queue should be moved to tracer
        # too much refactor work, leave to the next PR
        self._queue = Queue(capacity=8192)  # TODO: make this configurable
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
    # IRQ should do as less as possible, capture all the required context
    # information.
    # All the context insensitive processing (e.g. format time string,
    # serialization, validation, networking operation, file operation)
    # should be deferred to DPC.
    # The exporter can optionally provide the 4th API, transmit(data),
    # which can be used to transmit the data synchronously and return
    # the status to the caller.
    # This could be useful for auditing scenario.
    # One possible way of consuming the API is:
    # def on_span_end(self, span, span_data):
    #     payload = transform(span_data)
    #     self.transmit(payload)
    def emit(self, batch, event=None):
        raise NotImplementedError  # pragma: NO COVER

    # TODO: we shouldn't have this at the beginning
    # Tracer should own the queue, exporter shouldn't even know if the
    # source is a queue or not.
    # Tracer puts span_data into the queue.
    # Worker gets span_data from the src (here is the queue) and feed into
    # the dst (exporter).
    # Exporter defines the MTU (max_batch_size) and export_interval.
    # There can be one worker for each queue, or multiple workers for each
    # queue, or shared workers among queues (e.g. queue for traces, queue
    # for logs).
    def export(self, items):
        self._queue.puts(items, block=False)
