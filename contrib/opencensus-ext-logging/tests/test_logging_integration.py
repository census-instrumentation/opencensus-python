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

import mock

from opencensus.ext.logging import trace
from opencensus.log import TraceLogger
from opencensus.trace import config_integration
from opencensus.trace import execution_context
from opencensus.trace.tracers import noop_tracer


class TestLoggingIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._old_logger_class = logging.getLoggerClass()

    @classmethod
    def tearDownClass(cls):
        logging.setLoggerClass(cls._old_logger_class)

    def test_integration(self):
        self.assertEqual(self._old_logger_class, logging.getLoggerClass())
        config_integration.trace_integrations(['logging'])
        self.assertNotEqual(self._old_logger_class, logging.getLoggerClass())

    def test_trace_integration_set_tracer(self):
        mock_wrap = mock.Mock()
        patch_logging = mock.patch('logging.setLoggerClass', mock_wrap)

        with patch_logging:
            trace.trace_integration(tracer=noop_tracer.NoopTracer())

            # ensure the execution context has the right tracer
            self.assertIsInstance(execution_context.get_opencensus_tracer(),
                                    noop_tracer.NoopTracer)
            # ensure the correct logger is set
            mock_wrap.assert_called_once_with(TraceLogger)
