# Copyright 2018, OpenCensus Authors
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

import unittest
import mock
from opencensus.stats.exporters.transports import background_thread


class Test_Worker(unittest.TestCase):

    def _start_worker(self, worker):
        patch_thread = mock.patch('threading.Thread', new=_Thread)
        patch_atexit = mock.patch('atexit.register')

        with patch_thread as mock_thread:
            with patch_atexit as mock_atexit:
                worker.start()
                return mock_thread, mock_atexit

    def test_constructor(self):
        exporter = mock.Mock()
        grace_period = 10
        max_batch_size = 20

        worker = background_thread._Worker(exporter, grace_period=grace_period,
                                           max_batch_size=max_batch_size)

        self.assertEqual(worker.exporter, exporter)
        self.assertEqual(worker._grace_period, grace_period)
        self.assertEqual(worker._max_batch_size, max_batch_size)
        self.assertFalse(worker.is_alive)
        self.assertIsNone(worker._thread)

    def test_start(self):
        exporter = mock.Mock()
        worker = background_thread._Worker(exporter)

        mock_thread, mock_atexit = self._start_worker(worker)

        self.assertTrue(worker.is_alive)
        self.assertIsNotNone(worker._thread)
        self.assertTrue(worker._thread.daemon)
        self.assertEqual(worker._thread._target, worker._thread_main)
        self.assertEqual(
            worker._thread._name, background_thread._WORKER_THREAD_NAME)
        mock_atexit.assert_called_once_with(worker._export_pending_views)

        cur_thread = worker._thread
        self._start_worker(worker)
        self.assertIs(cur_thread, worker._thread)

    def test_stop(self):
        exporter = mock.Mock()
        worker = background_thread._Worker(exporter)

        mock_thread, mock_atexit = self._start_worker(worker)

        thread = worker._thread

        worker.stop()

        self.assertEqual(worker._queue.qsize(), 1)
        self.assertEqual(
            worker._queue.get(), background_thread._WORKER_TERMINATOR)
        self.assertFalse(worker.is_alive)
        self.assertIsNone(worker._thread)

        # If thread not alive, do not stop twice.
        worker.stop()

    def test__export_pending_views(self):
        exporter = mock.Mock()
        worker = background_thread._Worker(exporter)

        self._start_worker(worker)
        worker._export_pending_views()

        self.assertFalse(worker.is_alive)

        worker._export_pending_views()

    def test__export_pending_views_non_empty_queue(self):
        exporter = mock.Mock()
        worker = background_thread._Worker(exporter)

        self._start_worker(worker)
        worker.enqueue(mock.Mock())
        worker._export_pending_views()

        self.assertFalse(worker.is_alive)

    def test__export_pending_views_did_not_join(self):
        exporter = mock.Mock()
        worker = background_thread._Worker(exporter)

        self._start_worker(worker)
        worker._thread._terminate_on_join = False
        worker.enqueue(mock.Mock())
        worker._export_pending_views()

        self.assertFalse(worker.is_alive)

    def test__thread_main(self):
        exporter = mock.Mock()
        worker = background_thread._Worker(exporter)

        stat1 = {
            'statId': 'test1',
            'views': [{}, {}],
        }
        stat2 = {
            'statId': 'test2',
            'views': [{}],
        }

        worker.enqueue(stat1)
        worker.enqueue(stat2)
        worker._queue.put_nowait(background_thread._WORKER_TERMINATOR)

        worker._thread_main()

        self.assertTrue(worker.exporter.emit.called)
        self.assertEqual(worker._queue.qsize(), 0)

    def test__thread_main_batches(self):
        exporter = mock.Mock()
        worker = background_thread._Worker(exporter, max_batch_size=2)

        # Enqueue three records and the termination signal. This should be
        # enough to perform two separate batches and a third loop with just
        # the exit.
        stat1 = {
            'statId': 'test1',
            'views': [{}, {}],
        }
        stat2 = {
            'statId': 'test2',
            'views': [{}, {}],
        }
        stat3 = {
            'statId': 'test3',
            'views': [{}, {}],
        }
        stat4 = {
            'statId': 'test4',
            'views': [{}, {}],
        }
        worker.enqueue(stat1)
        worker.enqueue(stat2)
        worker.enqueue(stat3)
        worker.enqueue(stat4)

        worker._queue.put_nowait(background_thread._WORKER_TERMINATOR)

        worker._thread_main()

        self.assertEqual(worker._queue.qsize(), 0)

    def test__thread_main_terminate_before_finish(self):

        class Exporter(object):
            def __init__(self):
                self.exported = []

            def emit(self, span):
                self.exported.append(span)

        exporter = Exporter()
        worker = background_thread._Worker(exporter, max_batch_size=2)

        # Enqueue three records and the termination signal. This should be
        # enough to perform two separate batches and a third loop with just
        # the exit.
        worker._queue.put_nowait(background_thread._WORKER_TERMINATOR)

        # Worker should be terminated after sending span_data1, and
        # span_data2 won't be exported.
        view_data1 = [mock.Mock()]
        view_data2 = [mock.Mock()]

        worker.enqueue(view_data1)
        worker.enqueue(view_data2)

        worker._thread_main()

        self.assertEqual(exporter.exported, [view_data1])

        # trace2 should be left in the queue because worker is terminated.
        self.assertEqual(worker._queue.qsize(), 1)

    def test_flush(self):
        from six.moves import queue

        exporter = mock.Mock()
        worker = background_thread._Worker(exporter)
        worker._queue = mock.Mock(spec=queue.Queue)

        # Queue is empty, should not block.
        worker.flush()
        worker._queue.join.assert_called()


class TestBackgroundThreadTransport(unittest.TestCase):

    def test_constructor(self):
        patch_worker = mock.patch(
            'opencensus.stats.exporters.transports.background_thread._Worker',
            autospec=True)
        exporter = mock.Mock()

        with patch_worker as mock_worker:
            transport = background_thread.BackgroundThreadTransport(exporter)

        self.assertTrue(transport.worker.start.called)
        self.assertEqual(transport.exporter, exporter)

    def test_export(self):
        patch_worker = mock.patch(
            'opencensus.stats.exporters.transports.background_thread._Worker',
            autospec=True)
        exporter = mock.Mock()

        with patch_worker as mock_worker:
            transport = background_thread.BackgroundThreadTransport(exporter)

        stat = {
            'statId': 'test',
            'views': [{}, {}],
        }

        transport.export(stat)

        self.assertTrue(transport.worker.enqueue.called)

    def test_flush(self):
        patch_worker = mock.patch(
            'opencensus.stats.exporters.transports.background_thread._Worker',
            autospec=True)
        exporter = mock.Mock()

        with patch_worker as mock_worker:
            transport = background_thread.BackgroundThreadTransport(exporter)

            transport.flush()

            self.assertTrue(transport.worker.flush.called)


class _Thread(object):

    def __init__(self, target, name):
        self._target = target
        self._name = name
        self._timeout = None
        self._terminate_on_join = True
        self.daemon = False

    def is_alive(self):
        return self._is_alive

    def start(self):
        self._is_alive = True

    def stop(self):
        self._is_alive = False

    def join(self, timeout=None):
        self._timeout = timeout
        if self._terminate_on_join:
            self.stop()
