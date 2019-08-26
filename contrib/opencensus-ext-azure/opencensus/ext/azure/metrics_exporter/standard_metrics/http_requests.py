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

import sys
import time

from opencensus.metrics.export.gauge import DerivedDoubleGauge
if sys.version_info < (3,):
    from BaseHTTPServer import HTTPServer
else:
    from http.server import HTTPServer

requests_map = dict()
ORIGINAL_CONSTRUCTOR = HTTPServer.__init__


def request_patch(func):
    def wrapper(self=None):
        start_time = time.time()
        func(self)
        end_time = time.time()

        # Update count
        count = requests_map.get('count', 0)
        requests_map['count'] = count + 1

        # Update duration
        duration = requests_map.get('duration', 0)
        requests_map['duration'] = duration + (end_time - start_time)
    return wrapper


def server_patch(*args, **kwargs):
    if len(args) >= 3:
        handler = args[2]
        if handler:
            # Patch the handler methods if they exist
            if "do_DELETE" in dir(handler):
                handler.do_DELETE = request_patch(handler.do_DELETE)
            if "do_GET" in dir(handler):
                handler.do_GET = request_patch(handler.do_GET)
            if "do_HEAD" in dir(handler):
                handler.do_HEAD = request_patch(handler.do_HEAD)
            if "do_OPTIONS" in dir(handler):
                handler.do_OPTIONS = request_patch(handler.do_OPTIONS)
            if "do_POST" in dir(handler):
                handler.do_POST = request_patch(handler.do_POST)
            if "do_PUT" in dir(handler):
                handler.do_PUT = request_patch(handler.do_PUT)
    result = ORIGINAL_CONSTRUCTOR(*args, **kwargs)
    return result


def setup():
    # Patch the HTTPServer handler to track request information
    HTTPServer.__init__ = server_patch


def get_interval_requests_count():
    current_count = requests_map.get('count', 0)
    last_count = requests_map.get('last_count', 0)
    return current_count - last_count


class RequestsAvgExecutionMetric(object):
    NAME = "\\ASP.NET Applications(??APP_W3SVC_PROC??)\\Request Execution Time"

    def __init__(self):
        setup()

    @staticmethod
    def get_value():
        duration = requests_map.get('duration', 0)
        last_average_duration = requests_map.get('last_average_duration', 0)

        try:
            interval_count = get_interval_requests_count()
            request_duration = duration / interval_count

            requests_map['last_average_duration'] = request_duration
            # Reset duration
            requests_map['duration'] = 0
            # Convert to milliseconds
            return request_duration * 1000.0
        except ZeroDivisionError:
            # If interval_count is 0, exporter call made too close to previous
            # Return the previous result if this is the case
            return last_average_duration * 1000.0

    def __call__(self):
        """ Returns a derived gauge for incoming requests execution rate

        Calculated by getting the time it takes to make an incoming request
        and dividing over the amount of incoming requests over an elapsed time.

        :rtype: :class:`opencensus.metrics.export.gauge.DerivedLongGauge`
        :return: The gauge representing the incoming requests metric
        """
        gauge = DerivedDoubleGauge(
            RequestsAvgExecutionMetric.NAME,
            'Incoming Requests Average Execution Rate',
            'milliseconds',
            [])
        gauge.create_default_time_series(RequestsAvgExecutionMetric.get_value)
        return gauge


class RequestsRateMetric(object):
    NAME = "\\ASP.NET Applications(??APP_W3SVC_PROC??)\\Requests/Sec"

    def __init__(self):
        setup()

    @staticmethod
    def get_value():
        current_time = time.time()
        last_rate_time = requests_map.get('last_rate_time')
        last_rate = requests_map.get('last_rate', 0)

        try:
            # last_rate_time is None the first time this function is called
            if last_rate_time is not None:
                elapsed_seconds = current_time - last_rate_time
                interval_count = get_interval_requests_count()
                request_rate = interval_count / elapsed_seconds
            else:
                request_rate = 0
            requests_map['last_rate_time'] = current_time
            requests_map['last_count'] = requests_map.get('count', 0)
            requests_map['last_rate'] = request_rate

            return request_rate
        except ZeroDivisionError:
            # If elapsed_seconds is 0, exporter call made too close to previous
            # Return the previous result if this is the case
            return last_rate

    def __call__(self):
        """ Returns a derived gauge for incoming requests per second

        Calculated by obtaining by getting the number of incoming requests
        made to an HTTPServer within an elapsed time and dividing that value
        over the elapsed time.

        :rtype: :class:`opencensus.metrics.export.gauge.DerivedLongGauge`
        :return: The gauge representing the incoming requests metric
        """
        gauge = DerivedDoubleGauge(
            RequestsRateMetric.NAME,
            'Incoming Requests per second',
            'rps',
            [])
        gauge.create_default_time_series(RequestsRateMetric.get_value)
        return gauge
