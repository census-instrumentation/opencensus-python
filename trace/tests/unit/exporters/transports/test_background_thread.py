# Copyright 2017 Google Inc.
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

from opencensus.trace.exporters.transports import background_thread


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
        mock_atexit.assert_called_once_with(worker._export_pending_spans)

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

    def test__export_pending_spans(self):
        exporter = mock.Mock()
        worker = background_thread._Worker(exporter)

        self._start_worker(worker)
        worker._export_pending_spans()

        self.assertFalse(worker.is_alive)

        worker._export_pending_spans()

    def test__export_pending_spans_non_empty_queue(self):
        exporter = mock.Mock()
        worker = background_thread._Worker(exporter)

        self._start_worker(worker)
        worker.enqueue(mock.Mock())
        worker._export_pending_spans()

        self.assertFalse(worker.is_alive)

    def test__main_thread_terminated_did_not_join(self):
        exporter = mock.Mock()
        worker = background_thread._Worker(exporter)

        self._start_worker(worker)
        worker._thread._terminate_on_join = False
        worker.enqueue(mock.Mock())
        worker._export_pending_spans()

        self.assertFalse(worker.is_alive)

    def test__thread_main(self):
        exporter = mock.Mock()
        worker = background_thread._Worker(exporter)

        trace1 = {}
        trace2 = {}

        worker.enqueue(trace1)
        worker.enqueue(trace2)
        worker._queue.put_nowait(background_thread._WORKER_TERMINATOR)

        worker._thread_main()

        self.assertTrue(worker._cloud_logger._batch.commit_called)
        self.assertEqual(worker._cloud_logger._batch.commit_count, 2)
        self.assertEqual(worker._queue.qsize(), 0)

    def test__thread_main_error(self):
        from google.cloud.logging.handlers.transports import background_thread

        worker = self._make_one(_Logger(self.NAME))
        worker._cloud_logger._batch_cls = _RaisingBatch

        # Enqueue one record and the termination signal.
        self._enqueue_record(worker, '1')
        worker._queue.put_nowait(background_thread._WORKER_TERMINATOR)

        worker._thread_main()

        self.assertTrue(worker._cloud_logger._batch.commit_called)
        self.assertEqual(worker._queue.qsize(), 0)

    def test__thread_main_batches(self):
        from google.cloud.logging.handlers.transports import background_thread

        worker = self._make_one(_Logger(self.NAME), max_batch_size=2)

        # Enqueue three records and the termination signal. This should be
        # enough to perform two separate batches and a third loop with just
        # the exit.
        self._enqueue_record(worker, '1')
        self._enqueue_record(worker, '2')
        self._enqueue_record(worker, '3')
        self._enqueue_record(worker, '4')
        worker._queue.put_nowait(background_thread._WORKER_TERMINATOR)

        worker._thread_main()

        # The last batch should not have been executed because it had no items.
        self.assertFalse(worker._cloud_logger._batch.commit_called)
        self.assertEqual(worker._queue.qsize(), 0)

    def test_flush(self):
        worker = self._make_one(_Logger(self.NAME))
        worker._queue = mock.Mock(spec=queue.Queue)

        # Queue is empty, should not block.
        worker.flush()
        worker._queue.join.assert_called()


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
