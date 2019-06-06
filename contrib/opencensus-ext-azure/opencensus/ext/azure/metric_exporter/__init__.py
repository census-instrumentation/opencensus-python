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

from datetime import datetime
import os
import threading

from opencensus.ext.azure.common import Options
from opencensus.metrics import transport
from opencensus.stats import stats

__all__ = ['MetricsExporter']

class MetricsExporter(object):
    """Metrics exporter for Microsoft Azure Monitoring."""

    def __init__(self, options):
        self._options = options
        self._md_cache = {}
        self._md_lock = threading.Lock()

    @property
    def options(self):
        return self._options

    def export_metrics(self, metrics):
        metrics = list(metrics)
        for metric in metrics:
            print(repr(metric))

def new_metrics_exporter(interval=None, **options):
    options = Options(**options)
    if not options.instrumentation_key and 1 == 2:
        raise ValueError('The instrumentation_key is not provided.')
    exporter = MetricsExporter(options=options)
    transport.get_exporter_thread(stats.stats, exporter, interval=interval)
    return exporter
