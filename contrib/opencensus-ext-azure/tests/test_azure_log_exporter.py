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

import logging
import os
import shutil
import unittest

import mock

from opencensus.ext.azure import log_exporter

TEST_FOLDER = os.path.abspath('.test.logs')


def setUpModule():
    os.makedirs(TEST_FOLDER)


def tearDownModule():
    shutil.rmtree(TEST_FOLDER)


def throw(exc_type, *args, **kwargs):
    def func(*_args, **_kwargs):
        raise exc_type(*args, **kwargs)
    return func


class CustomLogHandler(log_exporter.BaseLogHandler):
    def __init__(self, max_batch_size, callback):
        self.export_interval = 1
        self.max_batch_size = max_batch_size
        self.callback = callback
        super(CustomLogHandler, self).__init__(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
        )

    def export(self, batch):
        return self.callback(batch)


class TestBaseLogHandler(unittest.TestCase):
    def test_basic(self):
        logger = logging.getLogger(self.id())
        handler = CustomLogHandler(10, lambda batch: None)
        logger.addHandler(handler)
        logger.warning('TEST')
        handler.flush()
        logger.warning('TEST')
        logger.removeHandler(handler)
        handler.close()

    def test_export_exception(self):
        logger = logging.getLogger(self.id())
        handler = CustomLogHandler(1, throw(Exception))
        logger.addHandler(handler)
        logger.warning('TEST')
        logger.removeHandler(handler)
        handler.flush()
        handler.close()


class TestAzureLogHandler(unittest.TestCase):
    def test_ctor(self):
        from opencensus.ext.azure.common import Options
        instrumentation_key = Options._default.instrumentation_key
        Options._default.instrumentation_key = None
        self.assertRaises(ValueError, lambda: log_exporter.AzureLogHandler())
        Options._default.instrumentation_key = instrumentation_key

    def test_invalid_sampling_rate(self):
        with self.assertRaises(ValueError):
            log_exporter.AzureLogHandler(
                instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
                logging_sampling_rate=4.0,
            )

    def test_init_handler_with_proxies(self):
        handler = log_exporter.AzureLogHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            proxies='{"https":"https://test-proxy.com"}',
        )

        self.assertEqual(
            handler.options.proxies,
            '{"https":"https://test-proxy.com"}',
        )

    def test_init_handler_with_queue_capacity(self):
        handler = log_exporter.AzureLogHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            queue_capacity=500,
        )

        self.assertEqual(
            handler.options.queue_capacity,
            500
        )

        self.assertEqual(
            handler._worker._src._queue.maxsize,
            500
        )

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_exception(self, requests_mock):
        logger = logging.getLogger(self.id())
        handler = log_exporter.AzureLogHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        logger.addHandler(handler)
        try:
            return 1 / 0  # generate a ZeroDivisionError
        except Exception:
            logger.exception('Captured an exception.')
        handler.close()
        self.assertEqual(len(requests_mock.call_args_list), 1)
        post_body = requests_mock.call_args_list[0][1]['data']
        self.assertTrue('ZeroDivisionError' in post_body)

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_exception_with_custom_properties(self, requests_mock):
        logger = logging.getLogger(self.id())
        handler = log_exporter.AzureLogHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        logger.addHandler(handler)
        try:
            return 1 / 0  # generate a ZeroDivisionError
        except Exception:
            properties = {
                'custom_dimensions':
                {
                        'key_1': 'value_1',
                        'key_2': 'value_2'
                }
            }
            logger.exception('Captured an exception.', extra=properties)
        handler.close()
        self.assertEqual(len(requests_mock.call_args_list), 1)
        post_body = requests_mock.call_args_list[0][1]['data']
        self.assertTrue('ZeroDivisionError' in post_body)
        self.assertTrue('key_1' in post_body)
        self.assertTrue('key_2' in post_body)

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_export_empty(self, request_mock):
        handler = log_exporter.AzureLogHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        handler._export([])
        self.assertEqual(len(os.listdir(handler.storage.path)), 0)
        handler.close()

    @mock.patch('opencensus.ext.azure.log_exporter'
                '.AzureLogHandler.log_record_to_envelope')
    def test_export_failure(self, log_record_to_envelope_mock):
        log_record_to_envelope_mock.return_value = ['bar']
        handler = log_exporter.AzureLogHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        with mock.patch('opencensus.ext.azure.log_exporter'
                        '.AzureLogHandler._transmit') as transmit:
            transmit.return_value = 10
            handler._export(['foo'])
        self.assertEqual(len(os.listdir(handler.storage.path)), 1)
        self.assertIsNone(handler.storage.get())
        handler.close()

    def test_log_record_to_envelope(self):
        handler = log_exporter.AzureLogHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        envelope = handler.log_record_to_envelope(mock.MagicMock(
            exc_info=None,
            levelno=10,
        ))
        self.assertEqual(
            envelope.iKey,
            '12345678-1234-5678-abcd-12345678abcd')
        handler.close()

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_log_record_with_custom_properties(self, requests_mock):
        logger = logging.getLogger(self.id())
        handler = log_exporter.AzureLogHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        logger.addHandler(handler)
        logger.warning('action', extra={
            'custom_dimensions':
                {
                    'key_1': 'value_1',
                    'key_2': 'value_2'
                }
            })
        handler.close()
        post_body = requests_mock.call_args_list[0][1]['data']
        self.assertTrue('action' in post_body)
        self.assertTrue('key_1' in post_body)
        self.assertTrue('key_2' in post_body)

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_log_with_invalid_custom_properties(self, requests_mock):
        logger = logging.getLogger(self.id())
        handler = log_exporter.AzureLogHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        logger.addHandler(handler)
        logger.warning('action_1_%s', None)
        logger.warning('action_2_%s', 'arg', extra={
            'custom_dimensions': 'not_a_dict'
        })
        logger.warning('action_3_%s', 'arg', extra={
            'notcustom_dimensions': {'key_1': 'value_1'}
        })

        handler.close()
        self.assertEqual(len(os.listdir(handler.storage.path)), 0)
        post_body = requests_mock.call_args_list[0][1]['data']
        self.assertTrue('action_1_' in post_body)
        self.assertTrue('action_2_arg' in post_body)
        self.assertTrue('action_3_arg' in post_body)

        self.assertFalse('not_a_dict' in post_body)
        self.assertFalse('key_1' in post_body)

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_log_record_sampled(self, requests_mock):
        logger = logging.getLogger(self.id())
        handler = log_exporter.AzureLogHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            logging_sampling_rate=1.0,
        )
        logger.addHandler(handler)
        logger.warning('Hello_World')
        logger.warning('Hello_World2')
        logger.warning('Hello_World3')
        logger.warning('Hello_World4')
        handler.close()
        post_body = requests_mock.call_args_list[0][1]['data']
        self.assertTrue('Hello_World' in post_body)
        self.assertTrue('Hello_World2' in post_body)
        self.assertTrue('Hello_World3' in post_body)
        self.assertTrue('Hello_World4' in post_body)

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_log_record_not_sampled(self, requests_mock):
        logger = logging.getLogger(self.id())
        handler = log_exporter.AzureLogHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            logging_sampling_rate=0.0,
        )
        logger.addHandler(handler)
        logger.warning('Hello_World')
        logger.warning('Hello_World2')
        logger.warning('Hello_World3')
        logger.warning('Hello_World4')
        handler.close()
        self.assertFalse(requests_mock.called)


class TestAzureEventHandler(unittest.TestCase):
    def test_ctor(self):
        from opencensus.ext.azure.common import Options
        instrumentation_key = Options._default.instrumentation_key
        Options._default.instrumentation_key = None
        self.assertRaises(ValueError, lambda: log_exporter.AzureEventHandler())
        Options._default.instrumentation_key = instrumentation_key

    def test_invalid_sampling_rate(self):
        with self.assertRaises(ValueError):
            log_exporter.AzureEventHandler(
                instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
                logging_sampling_rate=4.0,
            )

    def test_init_handler_with_proxies(self):
        handler = log_exporter.AzureEventHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            proxies='{"https":"https://test-proxy.com"}',
        )

        self.assertEqual(
            handler.options.proxies,
            '{"https":"https://test-proxy.com"}',
        )

    def test_init_handler_with_queue_capacity(self):
        handler = log_exporter.AzureEventHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            queue_capacity=500,
        )

        self.assertEqual(
            handler.options.queue_capacity,
            500
        )
        # pylint: disable=protected-access
        self.assertEqual(
            handler._worker._src._queue.maxsize,
            500
        )

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_exception(self, requests_mock):
        logger = logging.getLogger(self.id())
        handler = log_exporter.AzureEventHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        logger.addHandler(handler)
        try:
            return 1 / 0  # generate a ZeroDivisionError
        except Exception:
            logger.exception('Captured an exception.')
        handler.close()
        self.assertEqual(len(requests_mock.call_args_list), 1)
        post_body = requests_mock.call_args_list[0][1]['data']
        self.assertTrue('ZeroDivisionError' in post_body)

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_exception_with_custom_properties(self, requests_mock):
        logger = logging.getLogger(self.id())
        handler = log_exporter.AzureEventHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        logger.addHandler(handler)
        try:
            return 1 / 0  # generate a ZeroDivisionError
        except Exception:
            properties = {
                'custom_dimensions':
                {
                        'key_1': 'value_1',
                        'key_2': 'value_2'
                }
            }
            logger.exception('Captured an exception.', extra=properties)
        handler.close()
        self.assertEqual(len(requests_mock.call_args_list), 1)
        post_body = requests_mock.call_args_list[0][1]['data']
        self.assertTrue('ZeroDivisionError' in post_body)
        self.assertTrue('key_1' in post_body)
        self.assertTrue('key_2' in post_body)

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_export_empty(self, request_mock):
        handler = log_exporter.AzureEventHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        handler._export([])
        self.assertEqual(len(os.listdir(handler.storage.path)), 0)
        handler.close()

    @mock.patch('opencensus.ext.azure.log_exporter'
                '.AzureEventHandler.log_record_to_envelope')
    def test_export_failure(self, log_record_to_envelope_mock):
        log_record_to_envelope_mock.return_value = ['bar']
        handler = log_exporter.AzureEventHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        with mock.patch('opencensus.ext.azure.log_exporter'
                        '.AzureEventHandler._transmit') as transmit:
            transmit.return_value = 10
            handler._export(['foo'])
        self.assertEqual(len(os.listdir(handler.storage.path)), 1)
        self.assertIsNone(handler.storage.get())
        handler.close()

    def test_log_record_to_envelope(self):
        handler = log_exporter.AzureEventHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        envelope = handler.log_record_to_envelope(mock.MagicMock(
            exc_info=None,
            levelno=10,
        ))
        self.assertEqual(
            envelope.iKey,
            '12345678-1234-5678-abcd-12345678abcd')
        handler.close()

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_log_record_with_custom_properties(self, requests_mock):
        logger = logging.getLogger(self.id())
        handler = log_exporter.AzureEventHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        logger.addHandler(handler)
        logger.warning('action', extra={
            'custom_dimensions':
                {
                    'key_1': 'value_1',
                    'key_2': 'value_2'
                }
            })
        handler.close()
        post_body = requests_mock.call_args_list[0][1]['data']
        self.assertTrue('action' in post_body)
        self.assertTrue('key_1' in post_body)
        self.assertTrue('key_2' in post_body)

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_log_with_invalid_custom_properties(self, requests_mock):
        logger = logging.getLogger(self.id())
        handler = log_exporter.AzureEventHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        logger.addHandler(handler)
        logger.warning('action_1_%s', None)
        logger.warning('action_2_%s', 'arg', extra={
            'custom_dimensions': 'not_a_dict'
        })
        logger.warning('action_3_%s', 'arg', extra={
            'notcustom_dimensions': {'key_1': 'value_1'}
        })

        handler.close()
        self.assertEqual(len(os.listdir(handler.storage.path)), 0)
        post_body = requests_mock.call_args_list[0][1]['data']
        self.assertTrue('action_1_' in post_body)
        self.assertTrue('action_2_arg' in post_body)
        self.assertTrue('action_3_arg' in post_body)

        self.assertFalse('not_a_dict' in post_body)
        self.assertFalse('key_1' in post_body)

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_log_record_sampled(self, requests_mock):
        logger = logging.getLogger(self.id())
        handler = log_exporter.AzureEventHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            logging_sampling_rate=1.0,
        )
        logger.addHandler(handler)
        logger.warning('Hello_World')
        logger.warning('Hello_World2')
        logger.warning('Hello_World3')
        logger.warning('Hello_World4')
        handler.close()
        post_body = requests_mock.call_args_list[0][1]['data']
        self.assertTrue('Hello_World' in post_body)
        self.assertTrue('Hello_World2' in post_body)
        self.assertTrue('Hello_World3' in post_body)
        self.assertTrue('Hello_World4' in post_body)

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_log_record_not_sampled(self, requests_mock):
        logger = logging.getLogger(self.id())
        handler = log_exporter.AzureEventHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            logging_sampling_rate=0.0,
        )
        logger.addHandler(handler)
        logger.warning('Hello_World')
        logger.warning('Hello_World2')
        logger.warning('Hello_World3')
        logger.warning('Hello_World4')
        handler.close()
        self.assertFalse(requests_mock.called)
