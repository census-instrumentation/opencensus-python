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

import collections
import sys
import unittest

import mock
import requests

from opencensus.ext.azure.metrics_exporter import standard_metrics

if sys.version_info < (3,):
    from BaseHTTPServer import HTTPServer
else:
    from http.server import HTTPServer

ORIGINAL_FUNCTION = requests.Session.request
ORIGINAL_CONS = HTTPServer.__init__


class TestStandardMetrics(unittest.TestCase):
    def setUp(self):
        standard_metrics.http_requests.requests_map.clear()
        requests.Session.request = ORIGINAL_FUNCTION
        standard_metrics.http_requests.ORIGINAL_CONSTRUCTOR = ORIGINAL_CONS

    @mock.patch('opencensus.ext.azure.metrics_exporter'
                '.standard_metrics.register_metrics')
    def test_producer_ctor(self, avail_mock):
        standard_metrics.AzureStandardMetricsProducer()

        self.assertEqual(len(avail_mock.call_args_list), 1)

    def test_producer_get_metrics(self):
        producer = standard_metrics.AzureStandardMetricsProducer()
        metrics = producer.get_metrics()

        self.assertEqual(len(metrics), 6)

    def test_register_metrics(self):
        registry = standard_metrics.register_metrics()

        self.assertEqual(len(registry.get_metrics()), 6)

    def test_get_available_memory_metric(self):
        metric = standard_metrics.AvailableMemoryMetric()
        gauge = metric()

        self.assertEqual(gauge.descriptor.name, '\\Memory\\Available Bytes')

    @mock.patch('psutil.virtual_memory')
    def test_get_available_memory(self, psutil_mock):
        memory = collections.namedtuple('memory', 'available')
        vmem = memory(available=100)
        psutil_mock.return_value = vmem
        mem = standard_metrics.AvailableMemoryMetric.get_value()

        self.assertEqual(mem, 100)

    def test_get_process_private_bytes_metric(self):
        metric = standard_metrics.ProcessMemoryMetric()
        gauge = metric()

        # TODO: Refactor names to be platform generic
        self.assertEqual(gauge.descriptor.name,
                         '\\Process(??APP_WIN32_PROC??)\\Private Bytes')

    def test_get_process_private_bytes(self):
        with mock.patch('opencensus.ext.azure.metrics_exporter' +
                        '.standard_metrics.process.PROCESS') as process_mock:
            memory = collections.namedtuple('memory', 'rss')
            pmem = memory(rss=100)
            process_mock.memory_info.return_value = pmem
            mem = standard_metrics.ProcessMemoryMetric.get_value()

            self.assertEqual(mem, 100)

    @mock.patch('opencensus.ext.azure.metrics_exporter'
                '.standard_metrics.process.logger')
    def test_get_process_private_bytes_exception(self, logger_mock):
        with mock.patch('opencensus.ext.azure.metrics_exporter' +
                        '.standard_metrics.process.PROCESS') as process_mock:
            process_mock.memory_info.side_effect = Exception()
            standard_metrics.ProcessMemoryMetric.get_value()

            logger_mock.exception.assert_called()

    def test_get_processor_time_metric(self):
        metric = standard_metrics.ProcessorTimeMetric()
        gauge = metric()

        self.assertEqual(gauge.descriptor.name,
                         '\\Processor(_Total)\\% Processor Time')

    def test_get_processor_time(self):
        with mock.patch('psutil.cpu_times_percent') as processor_mock:
            cpu = collections.namedtuple('cpu', 'idle')
            cpu_times = cpu(idle=94.5)
            processor_mock.return_value = cpu_times
            processor_time = standard_metrics.ProcessorTimeMetric.get_value()

            self.assertEqual(processor_time, 5.5)

    def test_get_process_cpu_usage_metric(self):
        metric = standard_metrics.ProcessCPUMetric()
        gauge = metric()

        self.assertEqual(gauge.descriptor.name,
                         '\\Process(??APP_WIN32_PROC??)\\% Processor Time')

    @mock.patch('opencensus.ext.azure.metrics_exporter'
                '.standard_metrics.process.psutil')
    def test_get_process_cpu_usage(self, psutil_mock):
        with mock.patch('opencensus.ext.azure.metrics_exporter'
                        '.standard_metrics.process.PROCESS') as process_mock:
            process_mock.cpu_percent.return_value = 44.4
            psutil_mock.cpu_count.return_value = 2
            cpu_usage = standard_metrics.ProcessCPUMetric.get_value()

            self.assertEqual(cpu_usage, 22.2)

    @mock.patch('opencensus.ext.azure.metrics_exporter'
                '.standard_metrics.process.logger')
    def test_get_process_cpu_usage_exception(self, logger_mock):
        with mock.patch('opencensus.ext.azure.metrics_exporter'
                        '.standard_metrics.process.psutil') as psutil_mock:
            psutil_mock.cpu_count.return_value = None
            standard_metrics.ProcessCPUMetric.get_value()

            logger_mock.exception.assert_called()

    def test_request_patch(self):
        map = standard_metrics.http_requests.requests_map
        func = mock.Mock()
        new_func = standard_metrics.http_requests.request_patch(func)
        new_func()

        self.assertEqual(map['count'], 1)
        self.assertIsNotNone(map['duration'])
        self.assertEqual(len(func.call_args_list), 1)

    def test_server_patch(self):
        standard_metrics. \
            http_requests. \
            ORIGINAL_CONSTRUCTOR = lambda x, y, z: None
        with mock.patch('opencensus.ext.azure.metrics_exporter'
                        '.standard_metrics.http_requests'
                        '.request_patch') as request_mock:
            handler = mock.Mock()
            handler.do_DELETE.return_value = None
            handler.do_GET.return_value = None
            handler.do_HEAD.return_value = None
            handler.do_OPTIONS.return_value = None
            handler.do_POST.return_value = None
            handler.do_PUT.return_value = None
            result = standard_metrics. \
                http_requests. \
                server_patch(None, None, handler)
            handler.do_DELETE()
            handler.do_GET()
            handler.do_HEAD()
            handler.do_OPTIONS()
            handler.do_POST()
            handler.do_PUT()

            self.assertEqual(result, None)
            self.assertEqual(len(request_mock.call_args_list), 6)

    def test_server_patch_no_methods(self):
        standard_metrics. \
            http_requests. \
            ORIGINAL_CONSTRUCTOR = lambda x, y, z: None
        with mock.patch('opencensus.ext.azure.metrics_exporter'
                        '.standard_metrics.http_requests'
                        '.request_patch') as request_mock:
            handler = mock.Mock()
            result = standard_metrics. \
                http_requests. \
                server_patch(None, None, handler)
            handler.do_DELETE()
            handler.do_GET()
            handler.do_HEAD()
            handler.do_OPTIONS()
            handler.do_POST()
            handler.do_PUT()

            self.assertEqual(result, None)
            self.assertEqual(len(request_mock.call_args_list), 0)

    def test_server_patch_no_args(self):
        standard_metrics \
            .http_requests \
            .ORIGINAL_CONSTRUCTOR = lambda x, y: None
        r = standard_metrics.http_requests.server_patch(None, None)

        self.assertEqual(r, None)

    def test_server_patch_no_handler(self):
        standard_metrics \
            .http_requests \
            .ORIGINAL_CONSTRUCTOR = lambda x, y, z: None
        r = standard_metrics.http_requests.server_patch(None, None, None)

        self.assertEqual(r, None)

    def test_get_requests_rate_metric(self):
        metric = standard_metrics.RequestsRateMetric()
        gauge = metric()

        name = '\\ASP.NET Applications(??APP_W3SVC_PROC??)\\Requests/Sec'
        self.assertEqual(gauge.descriptor.name, name)

    def test_get_requests_rate_first_time(self):
        rate = standard_metrics.http_requests.get_requests_rate()

        self.assertEqual(rate, 0)

    @mock.patch('opencensus.ext.azure.metrics_exporter'
                '.standard_metrics.http_requests.time')
    def test_get_requests_rate(self, time_mock):
        time_mock.time.return_value = 100
        standard_metrics.http_requests.requests_map['last_time'] = 98
        standard_metrics.http_requests.requests_map['count'] = 4
        rate = standard_metrics.http_requests.get_requests_rate()

        self.assertEqual(rate, 2)

    @mock.patch('opencensus.ext.azure.metrics_exporter'
                '.standard_metrics.http_requests.time')
    def test_get_requests_rate_error(self, time_mock):
        time_mock.time.return_value = 100
        standard_metrics.http_requests.requests_map['last_rate'] = 5
        standard_metrics.http_requests.requests_map['last_time'] = 100
        result = standard_metrics.http_requests.get_requests_rate()

        self.assertEqual(result, 5)

    def test_get_requests_execution_metric(self):
        metric = standard_metrics.RequestsAvgExecutionMetric()
        gauge = metric()

        name = '\\ASP.NET Applications(??APP_W3SVC_PROC??)' \
               '\\Request Execution Time'
        self.assertEqual(gauge.descriptor.name, name)

    def test_get_requests_execution(self):
        map = standard_metrics.http_requests.requests_map
        map['duration'] = 0.1
        map['count'] = 10
        map['last_count'] = 5
        result = standard_metrics.http_requests.get_average_execution_time()

        self.assertEqual(result, 20)

    def test_get_requests_execution_error(self):
        map = standard_metrics.http_requests.requests_map
        map['duration'] = 0.1
        map['count'] = 10
        map['last_count'] = 10
        result = standard_metrics.http_requests.get_average_execution_time()

        self.assertEqual(result, 0)
