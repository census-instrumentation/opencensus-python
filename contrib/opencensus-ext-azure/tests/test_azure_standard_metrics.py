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

from opencensus.ext.azure.metrics_exporter import standard_metrics


class TestStandardMetrics(unittest.TestCase):
    @mock.patch('opencensus.ext.azure.metrics_exporter'
                '.standard_metrics.get_available_memory_metric')
    def test_producer_ctor(self, avail_mock):
        standard_metrics.AzureStandardMetricsProducer()

        self.assertEqual(len(avail_mock.call_args_list), 1)

    def test_producer_get_metrics(self):
        producer = standard_metrics.AzureStandardMetricsProducer()
        metrics = producer.get_metrics()

        self.assertEqual(len(metrics), 3)

    def test_get_available_memory_metric(self):
        gauge = standard_metrics.get_available_memory_metric()

        self.assertEqual(gauge.descriptor.name, '\\Memory\\Available Bytes')

    @mock.patch('psutil.virtual_memory')
    def test_get_available_memory(self, psutil_mock):
        memory = collections.namedtuple('memory', 'available')
        vmem = memory(available=100)
        psutil_mock.return_value = vmem
        mem = standard_metrics.get_available_memory()

        self.assertEqual(mem, 100)

    def test_get_process_private_bytes_metric(self):
        gauge = standard_metrics.get_process_private_bytes_metric()

        # TODO: Refactor names to be platform generic
        self.assertEqual(gauge.descriptor.name,
                         '\\Process(??APP_WIN32_PROC??)\\Private Bytes')

    def test_get_process_private_bytes(self):
        with mock.patch('psutil.Process') as process_mock:
            memory = collections.namedtuple('memory', 'rss')
            pmem = memory(rss=100)
            process = mock.Mock()
            process.memory_info.return_value = pmem
            process_mock.return_value = process
            mem = standard_metrics.get_process_private_bytes()

            self.assertEqual(mem, 100)

    @mock.patch('opencensus.ext.azure.metrics_exporter'
                '.standard_metrics.logger')
    def test_get_process_private_bytes_exception(self, logger_mock):
        with mock.patch('psutil.Process') as process_mock:
            process_mock.side_effect = Exception()
            standard_metrics.get_process_private_bytes()

            logger_mock.exception.assert_called()

    def test_get_processor_time_metric(self):
        gauge = standard_metrics.get_processor_time_metric()

        self.assertEqual(gauge.descriptor.name,
                         '\\Processor(_Total)\\% Processor Time')

    def test_get_processor_time(self):
        with mock.patch('psutil.cpu_times_percent') as processor_mock:
            cpu = collections.namedtuple('cpu', 'idle')
            cpu_times = cpu(idle=94.5)
            processor_mock.return_value = cpu_times
            processor_time = standard_metrics.get_processor_time()

            self.assertEqual(processor_time, 5.5)
