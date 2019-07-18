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

import requests
import time

from opencensus.metrics.export.gauge import DerivedDoubleGauge

dependency_map = dict()


def dependency_patch(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        count = dependency_map.get('count', 0)
        dependency_map['count'] = count + 1
    return wrapper

def setup():
    requests.get = dependency_patch(requests.get)
    requests.Session.get = dependency_patch(requests.Session.get)
    requests.post = dependency_patch(requests.post)
    requests.Session.post = dependency_patch(requests.Session.post)
    dependency_map['last_count'] = 0
    dependency_map['count'] = 0
    dependency_map['last_time'] = time.time()


class DependencyRateMetric(object):
    NAME = "\\ApplicationInsights\\Dependency Calls\/Sec"
    def __init__(self):
        setup()

    @staticmethod
    def get_value():
        current_time = time.time()
        last_time = dependency_map.get('last_time')
        last_count = dependency_map.get('last_count')
        current_count = dependency_map.get('count')

        if last_time is not None and last_count is not None and current_count is not None:
            elapsed_seconds = current_time - last_time
            interval_count = current_count - last_count
            result = interval_count / elapsed_seconds
        else:
            result = 0
        dependency_map['last_time'] = current_time
        dependency_map['last_count'] = current_count
        return result

    def __call__(self):
        """ Returns a derived gauge for available memory

        Available memory is defined as memory that can be given instantly to
        processes without the system going into swap.

        :rtype: :class:`opencensus.metrics.export.gauge.DerivedLongGauge`
        :return: The gauge representing the available memory metric
        """
        gauge = DerivedDoubleGauge(
            DependencyRateMetric.NAME,
            'Amount of available memory in bytes',
            'byte',
            [])
        gauge.create_default_time_series(DependencyRateMetric.get_value)
        return gauge
