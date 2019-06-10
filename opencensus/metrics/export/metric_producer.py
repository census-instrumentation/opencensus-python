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

import threading
from datetime import datetime

from opencensus.metrics.export.metrics_recorder import MetricsRecorder
from opencensus.metrics.export.view_manager import ViewManager

class MetricProducer(object):
    """MetricProducer defines a View Manager and a Metrics Recorder in order for the
    collection of Metrics
    """

    def __init__(self):
        self.metrics_recorder = MetricsRecorder()
        self.view_manager = ViewManager()

    def get_metrics(self):
        """Get a Metric for each of the view manager's registered views.

        Convert each registered view's associated `ViewData` into a `Metric` to
        be exported, using the current time for metric conversions.

        :rtype: Iterator[:class: `opencensus.metrics.export.metric.Metric`]
        """
        return self.view_manager.measure_to_view_map.get_metrics(
            datetime.utcnow())


class MetricProducerManager(object):
    """Container class for MetricProducers to be used by exporters.

    :type metric_producers: iterable(class: 'MetricProducer')
    :param metric_producers: Optional initial metric producers.
    """

    def __init__(self, metric_producers=None):
        if metric_producers is None:
            self.metric_producers = set()
        else:
            self.metric_producers = set(metric_producers)
        self.mp_lock = threading.Lock()

    def add(self, metric_producer):
        """Add a metric producer.

        :type metric_producer: :class: 'MetricProducer'
        :param metric_producer: The metric producer to add.
        """
        if metric_producer is None:
            raise ValueError
        with self.mp_lock:
            self.metric_producers.add(metric_producer)

    def remove(self, metric_producer):
        """Remove a metric producer.

        :type metric_producer: :class: 'MetricProducer'
        :param metric_producer: The metric producer to remove.
        """
        if metric_producer is None:
            raise ValueError
        try:
            with self.mp_lock:
                self.metric_producers.remove(metric_producer)
        except KeyError:
            pass

    def get_all(self):
        """Get the set of all metric producers.

        Get a copy of `metric_producers`. Prefer this method to using the
        attribute directly to avoid other threads adding/removing producers
        while you're reading it.

        :rtype: set(:class: `MetricProducer`)
        :return: A set of all metric producers at the time of the call.
        """
        with self.mp_lock:
            mps_copy = set(self.metric_producers)
        return mps_copy

metrics = MetricProducer()