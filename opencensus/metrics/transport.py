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
import queue
import threading

from opencensus.common import utils


logger = logging.getLogger(__name__)

DEFAULT_INTERVAL = 60
GRACE_PERIOD = 5


class TransportError(Exception):
    pass


class PeriodicTask(threading.Thread):
    """Thread that periodically calls a given function.

    :type func: function
    :param func: The function to call.

    :type interval: int or float
    :param interval: Seconds between calls to the function.
    """

    daemon = True

    def __init__(self, func, interval=None, **kwargs):
        super(PeriodicTask, self).__init__(**kwargs)
        if interval is None:
            interval = DEFAULT_INTERVAL
        self.func = func
        self.interval = interval
        self._stopped = threading.Event()

    def run(self):
        while not self._stopped.wait(self.interval):
            try:
                self.func()
            except TransportError as ex:
                logger.exception(ex)
                self.stop()
            except Exception:
                logger.exception("Error handling metric export")

    def stop(self):
        self._stopped.set()


class ManualTask(threading.Thread):
    """Thread that calls a given function on command.

    `ManualTask.go` calls `func` once and blocks until it completes,
    effectively simulating running `func` in the calling thread.

    :type func: function
    :param func: The function to call.
    """

    STOP = object()

    def __init__(self, func, **kwargs):
        super(ManualTask, self).__init__(**kwargs)
        self.func = func
        self.qq = queue.Queue()
        self._stopped = threading.Event()

    def run(self):
        while True:
            task = self.qq.get()
            if task == ManualTask.STOP:
                break

            try:
                self.func()
            except TransportError as ex:
                logger.exception(ex)
                self.stop()
            except Exception:
                logger.exception("Error handling metric export")
            finally:
                task.set()

    def go(self):
        if self._stopped.is_set():
            raise ValueError("Thread is stopped")
        ee = threading.Event()
        self.qq.put(ee)
        ee.wait(GRACE_PERIOD)

    def stop(self):
        self._stopped.set()
        self.qq.put(ManualTask.STOP)


def get_default_task_class():
    return PeriodicTask


def get_exporter_thread(metric_producer, exporter):
    """Get a running task that periodically exports metrics.

    Get a `PeriodicTask` (by default, see `get_default_task_class`) that
    exports periodically calls

        exporter.export_metrics(metric_producer.get_metrics())

    :type metric_producer:
        :class:`opencensus.metrics.export.metric_producer.MetricProducer`
    :param exporter: The producer to use to get metrics to export.

    :type exporter: :class:`opencensus.stats.base_exporter.MetricsExporter`
    :param exporter: The exporter to use to export metrics.

    :rtype: :class:`threading.Thread`
    :return: A running thread responsible calling the exporter.

    """
    weak_get = utils.get_weakref(metric_producer.get_metrics)
    weak_export = utils.get_weakref(exporter.export_metrics)

    def export_all():
        get = weak_get()
        if get is None:
            raise TransportError("Metric producer is not available")
        export = weak_export()
        if export is None:
            raise TransportError("Metric exporter is not available")
        export(get())

    tt = get_default_task_class()(export_all)
    tt.start()
    return tt
