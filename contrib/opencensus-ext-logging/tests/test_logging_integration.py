# Copyright 2017, OpenCensus Authors
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
import unittest
try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

from opencensus.trace import config_integration


class TestLoggingIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log_stream = StringIO()
        logging.basicConfig(
            format="%(message)s traceId=%(traceId)s",
            stream=cls.log_stream,
            level=logging.INFO,
        )
        cls._old_logger_factory = logging.getLogRecordFactory()

    @classmethod
    def tearDownClass(cls):
        logging.setLogRecordFactory(cls._old_logger_factory)

    def test_integration(self):
        self.assertEqual(self._old_logger_factory, logging.getLogRecordFactory())
        config_integration.trace_integrations(['logging'])
        self.assertNotEqual(self._old_logger_factory, logging.getLogRecordFactory())

    def test_logger(self):
        log_msg_before_integration = "catch logger_before_integration"
        log1 = logging.getLogger("log1")

        config_integration.trace_integrations(['logging'])

        log_after_integration = "catch logger_after_integration"
        log2 = logging.getLogger("log2")

        log1.info(log_msg_before_integration)
        log2.info(log_after_integration)

        all_logs = self.log_stream.getvalue()
        assert "{} traceId=".format(log_msg_before_integration) in all_logs
        assert "{} traceId=".format(log_after_integration) in all_logs
