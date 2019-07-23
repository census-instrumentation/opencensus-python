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
import mock
import unittest
import urllib3

from opencensus.ext.azure.metrics_exporter import standard_metrics

ORIGNAL_FUNCTION = urllib3.connectionpool.HTTPConnectionPool.urlopen


class TestStandardMetrics(unittest.TestCase):
    def setUp(self):
        standard_metrics.http_dependencies.dependency_map.clear()
        urllib3.connectionpool.HTTPConnectionPool.urlopen = ORIGNAL_FUNCTION

    @mock.patch('opencensus.ext.azure.metrics_exporter'
                '.standard_metrics.register_metrics')
    def test_producer_ctor(self, avail_mock):
        standard_metrics.AzureStandardMetricsProducer()

        self.assertEqual(len(avail_mock.call_args_list), 1)

    def test_producer_get_metrics(self):
        producer = standard_metrics.AzureStandardMetricsProducer()
        metrics = producer.get_metrics()

<<<<<<< HEAD
        self.assertEqual(len(metrics), 4)
=======
        self.assertEqual(len(metrics), 5)
>>>>>>> 7a69096516cadf7536d5b4e4137e4910846f89eb

    def test_register_metrics(self):
        registry = standard_metrics.register_metrics()

<<<<<<< HEAD
        self.assertEqual(len(registry.get_metrics()), 4)
=======
        self.assertEqual(len(registry.get_metrics()), 5)
>>>>>>> 7a69096516cadf7536d5b4e4137e4910846f89eb

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
<<<<<<< HEAD
                        '.standard_metrics.process.PROCESS') as process_mock:
=======
                '.standard_metrics.process.PROCESS') as process_mock:
>>>>>>> 7a69096516cadf7536d5b4e4137e4910846f89eb
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

    def test_dependency_patch(self):
        standard_metrics.http_dependencies.setup()

        self.assertNotEqual(urllib3.connectionpool.HTTPConnectionPool \
                       .urlopen, ORIGNAL_FUNCTION)

    def test_get_dependency_rate_metric(self):
        metric = standard_metrics.DependencyRateMetric()
        gauge = metric()

        self.assertEqual(gauge.descriptor.name,
            '\\ApplicationInsights\\Dependency Calls\/Sec')

    def test_get_dependency_rate_first_time(self):
        rate = standard_metrics.DependencyRateMetric.get_value()

        self.assertEqual(rate, 0)

    @mock.patch('opencensus.ext.azure.metrics_exporter'
                '.standard_metrics.http_dependencies.time')
    def test_get_dependency_rate(self, time_mock):
        time_mock.time.return_value = 100
        standard_metrics.http_dependencies.dependency_map['last_time'] = 98
        standard_metrics.http_dependencies.dependency_map['count'] = 4
        rate = standard_metrics.DependencyRateMetric.get_value()

        self.assertEqual(rate, 2)

    @mock.patch('opencensus.ext.azure.metrics_exporter'
                '.standard_metrics.http_dependencies.logger')
    @mock.patch('opencensus.ext.azure.metrics_exporter'
                '.standard_metrics.http_dependencies.time')
    def test_get_dependency_rate_error(self, time_mock, logger_mock):
        time_mock.time.return_value = 100
        standard_metrics.http_dependencies.dependency_map['last_time'] = 100
        standard_metrics.DependencyRateMetric.get_value()

        logger_mock.exception.assert_called()

