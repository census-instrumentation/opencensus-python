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

import logging
import json
import requests

from opencensus.ext.azure.common import Options
from opencensus.ext.azure.common import utils
from opencensus.ext.azure.common.exporter import BaseExporter

logger = logging.getLogger(__name__)

__all__ = ['AzureExporter', 'LogHandler']


class AzureExporter(BaseExporter):
    """An exporter that sends logs to Microsoft Azure Monitor.

    :type options: dict
    :param options: Options for the exporter. Defaults to None.
    """

    def __init__(self, **options):
        self.options = Options(**options)
        if not self.options.instrumentation_key:
            raise ValueError('The instrumentation_key is not provided.')
        super(AzureExporter, self).__init__(**options)

    def emit(self, batch, event=None):
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

    def close(self):
        pass

    def createLock(self):
        self.lock = None

    def emit(self, record):
        self.exporter.export([record])

    def flush(self, timeout=None):
        self.exporter._queue.flush(timeout=timeout)
