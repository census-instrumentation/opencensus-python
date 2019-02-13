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
import threading

from opencensus.metrics.export import metric_producer


class Registry(metric_producer.MetricProducer):
    """A collection of gauges to be exported together.

    Each registered gauge must have a unique `descriptor.name`.
    """

    def __init__(self):
        self.gauges = {}
        self._gauges_lock = threading.Lock()

    def __repr__(self):
        return ('{}(gauges={}'
                .format(
                    type(self).__name__,
                    self.gauges
                ))

    def add_gauge(self, gauge):
        """Add `gauge` to the registry and return it.

        Raises a `ValueError` if another gauge with the same name already
        exists in the registry.

        :type gauge: class:`opencensus.metrics.export.gauge.LongGauge` or
        class:`opencensus.metrics.export.gauge.DoubleGauge`
        :param gauge: The gauge to add to the registry.

        :rtype: class:`opencensus.metrics.export.gauge.LongGauge` or
        class:`opencensus.metrics.export.gauge.DoubleGauge`
        :return: The gauge that was added to the registry.
        """
        if gauge is None:
            raise ValueError
        name = gauge.descriptor.name
        with self._gauges_lock:
            if name in self.gauges:
                raise ValueError(
                    'Another gauge named "{}" is already registered'
                    .format(name))
            self.gauges[name] = gauge

    def get_metrics(self):
        """Get a metric for each gauge in the registry at the current time.

        :rtype: set(:class:`opencensus.metrics.export.metric.Metric`)
        :return: A set of `Metric`s, one for each registered gauge.
        """
        now = datetime.now()
        metrics = set()
        with self._gauges_lock:
            for gauge in self.gauges.values():
                metrics.add(gauge.get_metric(now))
        return metrics
