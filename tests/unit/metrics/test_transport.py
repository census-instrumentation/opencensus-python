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
INTERVAL = .05


class TestPeriodicTask(unittest.TestCase):

    def test_default_constructor(self):
        mock_func = mock.Mock()
        task = transport.PeriodicTask(mock_func)
        self.assertEqual(task.func, mock_func)
        self.assertEqual(task.interval, transport.DEFAULT_INTERVAL)

    def test_periodic_task_not_started(self):
        mock_func = mock.Mock()
        task = transport.PeriodicTask(mock_func, INTERVAL)
        time.sleep(INTERVAL + INTERVAL / 2.0)
        mock_func.assert_not_called()
        task.stop()

    def test_periodic_task(self):
        mock_func = mock.Mock()
        task = transport.PeriodicTask(mock_func, INTERVAL)
        task.start()
        mock_func.assert_not_called()
        time.sleep(INTERVAL + INTERVAL / 2.0)
        self.assertEqual(mock_func.call_count, 1)
        time.sleep(INTERVAL)
        self.assertEqual(mock_func.call_count, 2)
        time.sleep(INTERVAL)
        self.assertEqual(mock_func.call_count, 3)

    def test_periodic_task_stop(self):
        mock_func = mock.Mock()
        task = transport.PeriodicTask(mock_func, INTERVAL)
        task.start()
        time.sleep(INTERVAL + INTERVAL / 2.0)
        self.assertEqual(mock_func.call_count, 1)
        task.stop()
        time.sleep(INTERVAL)
        self.assertEqual(mock_func.call_count, 1)


@mock.patch('opencensus.metrics.transport.DEFAULT_INTERVAL', INTERVAL)
@mock.patch('opencensus.metrics.transport.logger')
class TestGetExporterThreadPeriodic(unittest.TestCase):

    def test_threaded_export(self, mock_logger):
        producer = mock.Mock()
        exporter = mock.Mock()
        metrics = mock.Mock()
        producer.get_metrics.return_value = metrics
        try:
            task = transport.get_exporter_thread(producer, exporter)
            producer.get_metrics.assert_not_called()
            exporter.export_metrics.assert_not_called()
            time.sleep(INTERVAL + INTERVAL / 2.0)
            producer.get_metrics.assert_called_once_with()
            exporter.export_metrics.assert_called_once_with(metrics)
        finally:
            task.stop()
            task.join()

    def test_producer_error(self, mock_logger):
        producer = mock.Mock()
        exporter = mock.Mock()

        producer.get_metrics.side_effect = ValueError()

        task = transport.get_exporter_thread(producer, exporter)
        time.sleep(INTERVAL + INTERVAL / 2.0)
        mock_logger.exception.assert_called()
        self.assertFalse(task._stopped.is_set())

    def test_producer_deleted(self, mock_logger):
        producer = mock.Mock()
        exporter = mock.Mock()
        task = transport.get_exporter_thread(producer, exporter)
        del producer
        gc.collect()
        time.sleep(INTERVAL + INTERVAL / 2.0)
        mock_logger.exception.assert_called()
        self.assertTrue(task._stopped.is_set())

    def test_exporter_deleted(self, mock_logger):
        producer = mock.Mock()
        exporter = mock.Mock()
        task = transport.get_exporter_thread(producer, exporter)
        del exporter
        gc.collect()
        time.sleep(INTERVAL + INTERVAL / 2.0)
        mock_logger.exception.assert_called()
        self.assertTrue(task._stopped.is_set())
