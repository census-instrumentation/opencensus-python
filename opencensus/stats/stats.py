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

from datetime import datetime

from opencensus.metrics.export.metric_producer import MetricProducer
from opencensus.stats.stats_recorder import StatsRecorder
from opencensus.stats.view_manager import ViewManager


class Stats(MetricProducer):
    """Stats defines a View Manager and a Stats Recorder in order for the
    collection of Stats
    """

    def __init__(self):
        self._stats_recorder = StatsRecorder()
        self._view_manager = ViewManager()

    @property
    def stats_recorder(self):
        """the current stats recorder for Stats"""
        return self._stats_recorder

    @property
    def view_manager(self):
        """the current view manager for Stats"""
        return self._view_manager

    def get_metrics(self):
        """Get a Metric for each of the view manager's registered views.

        Convert each registered view's associated `ViewData` into a `Metric` to
        be exported, using the current time for metric conversions.

        :rtype: Iterator[:class: `opencensus.metrics.export.metric.Metric`]
        """
        return self.view_manager.measure_to_view_map.get_metrics(
            datetime.now())
