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

from concurrent import futures
from contextlib import contextmanager
import gc
import logging
import sys
import threading
import time

from opencensus.metrics import transport

if sys.version_info < (3,):
    import unittest2 as unittest
    import mock
else:
    import unittest
    from unittest import mock


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


class TestManualTask(unittest.TestCase):

    def test_manual_task(self):
        mock_func = mock.Mock()
        task = transport.ManualTask(mock_func)
        try:
            task.start()
            mock_func.assert_not_called()
            task.go()
            self.assertEqual(mock_func.call_count, 1)
            task.go()
            self.assertEqual(mock_func.call_count, 2)
        finally:
            task.stop()

        with self.assertRaises(ValueError):
            task.go()
        self.assertEqual(mock_func.call_count, 2)

    def test_manual_task_finish_queue(self):
        """Check that we finish the work on the queue after stop signal."""
        lock = threading.Lock()
        count = mock.Mock()

        def sleep_and_inc():
            time.sleep(INTERVAL)
            with lock:
                count()

        mock_func = mock.Mock()
        mock_func.side_effect = sleep_and_inc

        task = transport.ManualTask(mock_func)
        task.start()

        num_threads = 5
        with futures.ThreadPoolExecutor(max_workers=num_threads) as tpe:
            for _ in range(num_threads):
                tpe.submit(task.go)

            self.assertEqual(count.call_count, 0)
            # Call stop after work is queued, but not complete
            task.stop()

            time.sleep(num_threads * INTERVAL + INTERVAL / 2.0)
            self.assertEqual(count.call_count, num_threads)
            self.assertEqual(mock_func.call_count, num_threads)


@contextmanager
def patch_get_exporter_thread():
    with mock.patch('opencensus.metrics.transport'
                    '.get_default_task_class') as mm:
        mm.return_value = transport.ManualTask
        yield


class TestGetExporterThreadManual(unittest.TestCase):

    def test_threaded_export(self):
        with patch_get_exporter_thread():
            producer = mock.Mock()
            exporter = mock.Mock()
            metrics = mock.Mock()
            producer.get_metrics.return_value = metrics
            try:
                task = transport.get_exporter_thread(producer, exporter)
                producer.get_metrics.assert_not_called()
                exporter.export_metrics.assert_not_called()
                task.go()
                producer.get_metrics.assert_called_once_with()
                exporter.export_metrics.assert_called_once_with(metrics)
            finally:
                task.stop()

    def test_producer_error(self):
        producer = mock.Mock()
        exporter = mock.Mock()

        producer.get_metrics.side_effect = ValueError()

        with patch_get_exporter_thread():
            try:
                task = transport.get_exporter_thread(producer, exporter)
                with self.assertLogs('opencensus.metrics.transport',
                                     level=logging.ERROR):
                    task.go()
                self.assertFalse(task._stopped.is_set())
            finally:
                task.stop()

    def test_producer_deleted(self):
        with patch_get_exporter_thread():
            producer = mock.Mock()
            exporter = mock.Mock()
            task = transport.get_exporter_thread(producer, exporter)
            del producer
            gc.collect()
            with self.assertLogs('opencensus.metrics.transport',
                                 level=logging.ERROR):
                task.go()
            self.assertTrue(task._stopped.is_set())

    def test_exporter_deleted(self):
        with patch_get_exporter_thread():
            producer = mock.Mock()
            exporter = mock.Mock()
            task = transport.get_exporter_thread(producer, exporter)
            del exporter
            gc.collect()
            with self.assertLogs('opencensus.metrics.transport',
                                 level=logging.ERROR):
                task.go()
            self.assertTrue(task._stopped.is_set())


@mock.patch('opencensus.metrics.transport.DEFAULT_INTERVAL', INTERVAL)
class TestGetExporterThreadPeriodic(unittest.TestCase):

    def test_threaded_export(self):
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

    def test_producer_error(self):
        producer = mock.Mock()
        exporter = mock.Mock()

        producer.get_metrics.side_effect = ValueError()

        task = transport.get_exporter_thread(producer, exporter)
        with self.assertLogs('opencensus.metrics.transport',
                             level=logging.ERROR):
            time.sleep(INTERVAL + INTERVAL / 2.0)
        self.assertFalse(task._stopped.is_set())

    def test_producer_deleted(self):
        producer = mock.Mock()
        exporter = mock.Mock()
        task = transport.get_exporter_thread(producer, exporter)
        del producer
        gc.collect()
        with self.assertLogs('opencensus.metrics.transport',
                             level=logging.ERROR):
            time.sleep(INTERVAL + INTERVAL / 2.0)
        self.assertTrue(task._stopped.is_set())

    def test_exporter_deleted(self):
        producer = mock.Mock()
        exporter = mock.Mock()
        task = transport.get_exporter_thread(producer, exporter)
        del exporter
        gc.collect()
        with self.assertLogs('opencensus.metrics.transport',
                             level=logging.ERROR):
            time.sleep(INTERVAL + INTERVAL / 2.0)
        self.assertTrue(task._stopped.is_set())
