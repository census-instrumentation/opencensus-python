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

from opencensus.common.transports import async_


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

        worker = async_._Worker(exporter, grace_period=grace_period,
                                max_batch_size=max_batch_size)

        self.assertEqual(worker.exporter, exporter)
        self.assertEqual(worker._grace_period, grace_period)
        self.assertEqual(worker._max_batch_size, max_batch_size)
        self.assertFalse(worker.is_alive)
        self.assertIsNone(worker._thread)

    def test_start(self):
        exporter = mock.Mock()
        worker = async_._Worker(exporter)

        mock_thread, mock_atexit = self._start_worker(worker)

        self.assertTrue(worker.is_alive)
        self.assertIsNotNone(worker._thread)
        self.assertTrue(worker._thread.daemon)
        self.assertEqual(worker._thread._target, worker._thread_main)
        self.assertEqual(
            worker._thread._name, async_._WORKER_THREAD_NAME)
        mock_atexit.assert_called_once_with(worker._export_pending_data)

        cur_thread = worker._thread
        self._start_worker(worker)
        self.assertIs(cur_thread, worker._thread)

    def test_stop(self):
        exporter = mock.Mock()
        worker = async_._Worker(exporter)

        mock_thread, mock_atexit = self._start_worker(worker)

        worker.stop()

        self.assertEqual(worker._queue.qsize(), 1)
        self.assertEqual(
            worker._queue.get(), async_._WORKER_TERMINATOR)
        self.assertFalse(worker.is_alive)
        self.assertIsNone(worker._thread)

        # If thread not alive, do not stop twice.
        worker.stop()

    def test__export_pending_data(self):
        exporter = mock.Mock()
        worker = async_._Worker(exporter)

        self._start_worker(worker)
        worker._export_pending_data()

        self.assertFalse(worker.is_alive)

        worker._export_pending_data()

    def test__export_pending_data_non_empty_queue(self):
        exporter = mock.Mock()
        worker = async_._Worker(exporter)

        self._start_worker(worker)
        worker.enqueue(mock.Mock())
        worker._export_pending_data()

        self.assertFalse(worker.is_alive)

    def test__export_pending_data_did_not_join(self):
        exporter = mock.Mock()
        worker = async_._Worker(exporter)

        self._start_worker(worker)
        worker._thread._terminate_on_join = False
        worker.enqueue(mock.Mock())
        worker._export_pending_data()

        self.assertFalse(worker.is_alive)

    def test__thread_main(self):
        exporter = mock.Mock()
        worker = async_._Worker(exporter, wait_period=0)

        trace1 = {
            'traceId': 'test1',
            'spans': [{}, {}],
            }
        trace2 = {
            'traceId': 'test2',
            'spans': [{}],
        }

        worker.enqueue(trace1)
        worker.enqueue(trace2)
        worker._queue.put_nowait(async_._WORKER_TERMINATOR)

        worker._thread_main()

        self.assertTrue(worker.exporter.emit.called)
        self.assertEqual(worker._queue.qsize(), 0)

    def test__thread_main_batches(self):
        exporter = mock.Mock()
        worker = async_._Worker(exporter, max_batch_size=2, wait_period=0)

        # Enqueue three records and the termination signal. This should be
        # enough to perform two separate batches and a third loop with just
        # the exit.
        trace1 = {
            'traceId': 'test1',
            'spans': [{}, {}],
        }
        trace2 = {
            'traceId': 'test2',
            'spans': [{}, {}],
        }
        trace3 = {
            'traceId': 'test3',
            'spans': [{}, {}],
        }
        trace4 = {
            'traceId': 'test4',
            'spans': [{}, {}],
        }
        worker.enqueue(trace1)
        worker.enqueue(trace2)
        worker.enqueue(trace3)
        worker.enqueue(trace4)

        worker._queue.put_nowait(async_._WORKER_TERMINATOR)

        worker._thread_main()

        self.assertEqual(worker._queue.qsize(), 0)

    def test__thread_main_terminate_before_finish(self):

        class Exporter(object):
            def __init__(self):
                self.exported = []

            def emit(self, span):
                self.exported.append(span)

        exporter = Exporter()
        worker = async_._Worker(exporter, max_batch_size=2, wait_period=0)

        # Enqueue three records and the termination signal. This should be
        # enough to perform two separate batches and a third loop with just
        # the exit.
        worker._queue.put_nowait(async_._WORKER_TERMINATOR)

        # Worker should be terminated after sending span_data1, and
        # span_data2 won't be exported.
        span_data1 = [mock.Mock()]
        span_data2 = [mock.Mock()]

        worker.enqueue(span_data1)
        worker.enqueue(span_data2)

        worker._thread_main()

        self.assertEqual(exporter.exported, [span_data1])

        # trace2 should be left in the queue because worker is terminated.
        self.assertEqual(worker._queue.qsize(), 1)

    @mock.patch('opencensus.common.transports.async_.logger.exception')
    def test__thread_main_alive_on_emit_failed(self, mock):

        class Exporter(object):
            def __init__(self):
                self.exported = []

            def emit(self, span):
                if len(self.exported) < 2:
                    self.exported.extend(span)
                else:
                    raise Exception("This exporter is broken !")

        exporter = Exporter()
        worker = async_._Worker(exporter, max_batch_size=2, wait_period=0)

        span_data0 = [mock.Mock()]
        span_data1 = [mock.Mock()]
        span_data2 = [mock.Mock()]

        worker.enqueue(span_data0)
        worker.enqueue(span_data1)
        worker.enqueue(span_data2)
        worker.enqueue(async_._WORKER_TERMINATOR)

        worker._thread_main()

        # Span 2 should throw an exception, only span 0 and 1 are left
        self.assertEqual(exporter.exported, span_data0 + span_data1)

        # Logging exception should have been called on the exporter exception
        expected = '%s failed to emit data.Dropping %s objects from queue.'
        mock.assert_called_with(expected, 'Exporter', 1)

        # Nothing should be left in the queue because worker is terminated
        # and the data was dropped.
        self.assertEqual(worker._queue.qsize(), 0)

    def test_flush(self):
        from six.moves import queue

        exporter = mock.Mock()
        worker = async_._Worker(exporter)
        worker._queue = mock.Mock(spec=queue.Queue)

        # Queue is empty, should not block.
        worker.flush()
        worker._queue.join.assert_called()


class TestAsyncTransport(unittest.TestCase):

    def test_constructor(self):
        patch_worker = mock.patch(
            'opencensus.common.transports.async_._Worker',
            autospec=True)
        exporter = mock.Mock()

        with patch_worker:
            transport = async_.AsyncTransport(exporter)

        self.assertTrue(transport.worker.start.called)
        self.assertEqual(transport.exporter, exporter)

    def test_export(self):
        patch_worker = mock.patch(
            'opencensus.common.transports.async_._Worker',
            autospec=True)
        exporter = mock.Mock()

        with patch_worker:
            transport = async_.AsyncTransport(exporter)

        trace = {
            'traceId': 'test',
            'spans': [{}, {}],
        }

        transport.export(trace)

        self.assertTrue(transport.worker.enqueue.called)

    def test_flush(self):
        patch_worker = mock.patch(
            'opencensus.common.transports.async_._Worker',
            autospec=True)
        exporter = mock.Mock()

        with patch_worker:
            transport = async_.AsyncTransport(exporter)

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
