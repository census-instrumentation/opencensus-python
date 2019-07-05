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

import psutil

from opencensus.metrics.export.gauge import DerivedLongGauge
from opencensus.metrics.export.gauge import Registry
from opencensus.metrics.export.metric_producer import MetricProducer


class StandardMetricsProducer(Registry):
    """Implementation of the producer of standard metrics
        using gauges
    """
    def __init__(self):
        super(StandardMetricsProducer, self).__init__()

    """
    :type metrics: list
    :param metrics: the list of standard metrics
        :class:`BaseStandardMetric`
    """
    def register_metrics(self, metrics):
        for metric in metrics:
            metric.register(self)

    def get_metrics(self):
        for metric in super(StandardMetricsProducer, self).get_metrics():
            yield metric

class BaseStandardMetric(object):

    def register(self, registry):
        """Register this standard metric to the given registry
            Classes will override this method based on the type
            of standard metric
        """
        raise NotImplementedError  # pragma: NO COVER
