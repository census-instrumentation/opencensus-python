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
        func(self)
        count = requests_map.get('count', 0)
        requests_map['count'] = count + 1
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


class RequestsRateMetric(object):
    NAME = "\\ASP.NET Applications(??APP_W3SVC_PROC??)\\Requests/Sec"

    def __init__(self):
        setup()

    @staticmethod
    def get_value():
        current_count = requests_map.get('count', 0)
        current_time = time.time()
        last_count = requests_map.get('last_count', 0)
        last_time = requests_map.get('last_time')
        last_result = requests_map.get('last_result', 0)

        try:
            # last_time is None the very first time this function is called
            if last_time is not None:
                elapsed_seconds = current_time - last_time
                interval_count = current_count - last_count
                result = interval_count / elapsed_seconds
            else:
                result = 0
            requests_map['last_time'] = current_time
            requests_map['last_count'] = current_count
            requests_map['last_result'] = result
            return result
        except ZeroDivisionError:
            # If elapsed_seconds is 0, exporter call made too close to previous
            # Return the previous result if this is the case
            return last_result

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
