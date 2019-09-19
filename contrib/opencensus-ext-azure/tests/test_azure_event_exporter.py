import logging
import os
import shutil
import unittest

import mock

from opencensus.ext.azure import events_exporter

TEST_FOLDER = os.path.abspath('.test.logs')


def setUpModule():
    os.makedirs(TEST_FOLDER)


def tearDownModule():
    shutil.rmtree(TEST_FOLDER)


class TestAzureEventHandler(unittest.TestCase):
    def test_log_record_to_envelope(self):
        handler = events_exporter.AzureEventHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        envelope = handler.log_record_to_envelope(mock.MagicMock(
            msg="test"
        ))
        self.assertEqual(
            envelope.iKey,
            '12345678-1234-5678-abcd-12345678abcd')

        self.assertEqual(
            envelope.name,
            'Microsoft.ApplicationInsights.Event')

        self.assertEqual(
            envelope.get("data").baseData.get("name"),
            "test")
        handler.close()

    def test_log_record_to_envelope_with_properties(self):
        handler = events_exporter.AzureEventHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        envelope = handler.log_record_to_envelope(mock.MagicMock(
            msg="test",
            args={"sku": "SKU-12312"}
        ))
        self.assertEqual(
            len(envelope.get("data").baseData.get("properties")),
            1)
        handler.close()

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_export(self, requests_mock):
        logger = logging.getLogger(self.id())
        handler = events_exporter.AzureEventHandler(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        logger.addHandler(handler)
        logger.warning('test_metric')
        handler.close()
        self.assertEqual(len(requests_mock.call_args_list), 1)
        post_body = requests_mock.call_args_list[0][1]['data']
        self.assertTrue('test_metric' in post_body)
