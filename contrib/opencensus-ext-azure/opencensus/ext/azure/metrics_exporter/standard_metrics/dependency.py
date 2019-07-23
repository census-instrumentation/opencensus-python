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
import requests
import time

from opencensus.metrics.export.gauge import DerivedDoubleGauge

dependency_map = dict()
logger = logging.getLogger(__name__)
ORIGINAL_REQUEST = requests.Session.request


def dependency_patch(*args, **kwargs):
    # Disable collection if flag is set
    disable = kwargs.pop('disableCollection', None)
    result = ORIGINAL_REQUEST(*args, **kwargs)
    if disable is None or not disable:
        count = dependency_map.get('count', 0)
        dependency_map['count'] = count + 1
    return result


def setup():
    # Patch the requests library functions to track dependency information
    requests.Session.request = dependency_patch


class DependencyRateMetric(object):
    # Dependency call metrics can be found under custom metrics
    NAME = "\\ApplicationInsights\\Dependency Calls\/Sec"
    def __init__(self):
        setup()

    @staticmethod
    def get_value():
        current_time = time.time()
        last_time = dependency_map.get('last_time')
        last_count = dependency_map.get('last_count', 0)
        current_count = dependency_map.get('count', 0)

        try:
            # last_time is None the very first time this function is called
            if last_time is not None:
                elapsed_seconds = current_time - last_time
                interval_count = current_count - last_count
                result = interval_count / elapsed_seconds
            else:
                result = 0
            dependency_map['last_time'] = current_time
            dependency_map['last_count'] = current_count
            return result
        except ZeroDivisionError:
            logger.exception('Error handling get outgoing request rate. '
                             'Call made too close to previous call.')


    def __call__(self):
        """ Returns a derived gauge for outgoing requests per second

        Calculated by obtaining by getting the number of outgoing requests made
        using the requests library within an elapsed time and dividing that
        value over the elapsed time.

        :rtype: :class:`opencensus.metrics.export.gauge.DerivedLongGauge`
        :return: The gauge representing the available memory metric
        """
        gauge = DerivedDoubleGauge(
            DependencyRateMetric.NAME,
            'Outgoing Requests per second',
            'rps',
            [])
        gauge.create_default_time_series(DependencyRateMetric.get_value)
        return gauge
