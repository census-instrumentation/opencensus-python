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

import gc
import sys
import time

import mock

from opencensus.metrics import transport

if sys.version_info < (3,):
    import unittest2 as unittest
else:
    import unittest


# Some tests use real time! This is the time to wait between the exporter
# thread handling tasks, and doesn't account for processing time. If these
# tests become flaky, try increasing this.
INTERVAL = .1


class TestPeriodicMetricTask(unittest.TestCase):

    def test_default_constructor(self):
        mock_func = mock.Mock()
        task = transport.PeriodicMetricTask(function=mock_func)
        self.assertEqual(task.func, mock_func)
        self.assertEqual(task.interval, transport.DEFAULT_INTERVAL)

    def test_periodic_task_not_started(self):
        mock_func = mock.Mock()
        task = transport.PeriodicMetricTask(INTERVAL, mock_func)
        time.sleep(INTERVAL + INTERVAL / 2.0)
        mock_func.assert_not_called()
        task.cancel()

    def test_periodic_task(self):
        mock_func = mock.Mock()
        task = transport.PeriodicMetricTask(INTERVAL, mock_func)
        task.start()
        mock_func.assert_not_called()
        time.sleep(INTERVAL + INTERVAL / 2.0)
        self.assertEqual(mock_func.call_count, 1)
        time.sleep(INTERVAL)
        self.assertEqual(mock_func.call_count, 2)
        time.sleep(INTERVAL)
        self.assertEqual(mock_func.call_count, 3)

    def test_periodic_task_cancel(self):
        mock_func = mock.Mock()
        task = transport.PeriodicMetricTask(INTERVAL, mock_func)
        task.start()
        time.sleep(INTERVAL + INTERVAL / 2.0)
        self.assertEqual(mock_func.call_count, 1)
        task.cancel()
        time.sleep(INTERVAL)
        self.assertEqual(mock_func.call_count, 1)


@mock.patch('opencensus.metrics.transport.DEFAULT_INTERVAL', INTERVAL)
@mock.patch('opencensus.metrics.transport.logger')
class TestGetExporterThreadPeriodic(unittest.TestCase):

    @mock.patch('opencensus.metrics.transport.itertools.chain')
    def test_threaded_export(self, iter_mock, mock_logger):
        producer = mock.Mock()
        exporter = mock.Mock()
        metrics = mock.Mock()
        producer.get_metrics.return_value = metrics
        iter_mock.return_value = producer.get_metrics.return_value
        try:
            task = transport.get_exporter_thread([producer], exporter)
            producer.get_metrics.assert_not_called()
            exporter.export_metrics.assert_not_called()
            time.sleep(INTERVAL + INTERVAL / 2.0)
            producer.get_metrics.assert_called_once_with()
            exporter.export_metrics.assert_called_once_with(metrics)
        finally:
            task.cancel()
            task.join()

    def test_producer_error(self, mock_logger):
        producer = mock.Mock()
        exporter = mock.Mock()

        producer.get_metrics.side_effect = ValueError()

        task = transport.get_exporter_thread([producer], exporter)
        time.sleep(INTERVAL + INTERVAL / 2.0)
        mock_logger.exception.assert_called()
        self.assertFalse(task.finished.is_set())

    def test_producer_deleted(self, mock_logger):
        producer = mock.Mock()
        exporter = mock.Mock()
        task = transport.get_exporter_thread([producer], exporter)
        del producer
        gc.collect()
        time.sleep(INTERVAL + INTERVAL / 2.0)
        mock_logger.exception.assert_called()
        self.assertTrue(task.finished.is_set())

    def test_exporter_deleted(self, mock_logger):
        producer = mock.Mock()
        exporter = mock.Mock()
        task = transport.get_exporter_thread([producer], exporter)
        del exporter
        gc.collect()
        time.sleep(INTERVAL + INTERVAL / 2.0)
        mock_logger.exception.assert_called()
        self.assertTrue(task.finished.is_set())

    @mock.patch('opencensus.metrics.transport.itertools.chain')
    def test_multiple_producers(self, iter_mock, mock_logger):
        producer1 = mock.Mock()
        producer2 = mock.Mock()
        producers = [producer1, producer2]
        exporter = mock.Mock()
        metrics = mock.Mock()
        producer1.get_metrics.return_value = metrics
        producer2.get_metrics.return_value = metrics
        iter_mock.return_value = metrics
        try:
            task = transport.get_exporter_thread(producers, exporter)
            producer1.get_metrics.assert_not_called()
            producer2.get_metrics.assert_not_called()
            exporter.export_metrics.assert_not_called()
            time.sleep(INTERVAL + INTERVAL / 2.0)
            producer1.get_metrics.assert_called_once_with()
            producer2.get_metrics.assert_called_once_with()
            exporter.export_metrics.assert_called_once_with(metrics)
        finally:
            task.cancel()
            task.join()
