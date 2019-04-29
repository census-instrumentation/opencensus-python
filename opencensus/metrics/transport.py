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

from opencensus.common import utils
from opencensus.common.schedule import PeriodicTask


logger = logging.getLogger(__name__)

DEFAULT_INTERVAL = 60
GRACE_PERIOD = 5


class TransportError(Exception):
    pass


class MetricExporterTask(PeriodicTask):
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

    daemon = True

    def __init__(self, interval=None, function=None, args=None, kwargs=None):
        if interval is None:
            interval = DEFAULT_INTERVAL

        self.func = function

        def func(*aa, **kw):
            try:
                return self.func(*aa, **kw)
            except TransportError as ex:
                logger.exception(ex)
                self.cancel()
            except Exception:
                logger.exception("Error handling metric export")

        super(MetricExporterTask, self).__init__(interval, func, args, kwargs)


def get_exporter_thread(metric_producer, exporter, interval=None):
    """Get a running task that periodically exports metrics.

    Get a `PeriodicTask` that periodically calls:

        exporter.export_metrics(metric_producer.get_metrics())

    :type metric_producer:
        :class:`opencensus.metrics.export.metric_producer.MetricProducer`
    :param exporter: The producer to use to get metrics to export.

    :type exporter: :class:`opencensus.stats.base_exporter.MetricsExporter`
    :param exporter: The exporter to use to export metrics.

    :type interval: int or float
    :param interval: Seconds between export calls.

    :rtype: :class:`PeriodicTask`
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

    tt = MetricExporterTask(interval, export_all)
    tt.start()
    return tt
