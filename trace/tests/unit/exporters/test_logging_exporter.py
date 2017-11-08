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

import mock
import logging
import unittest

from opencensus.trace.exporters import logging_exporter


class TestLoggingExporter(unittest.TestCase):

    def test_constructor_default(self):
        exporter = logging_exporter.LoggingExporter()

        self.assertIn(exporter.handler, logging.getLogger().handlers)
        assert isinstance(exporter.handler, logging.StreamHandler)

    def test_constructor_explicit(self):
        handler = _Handler(logging.INFO)
        exporter = logging_exporter.LoggingExporter(handler=handler)

        self.assertIn(exporter.handler, logging.getLogger().handlers)

    def test_emit(self):
        exporter = logging_exporter.LoggingExporter()
        logger = mock.Mock()
        exporter.logger = logger

        traces = '{traces: test}'
        exporter.emit(traces)

        logger.info.assert_called_once_with(traces)

    def test_export(self):
        exporter = logging_exporter.LoggingExporter()
        exporter.export({})

        self.assertTrue(exporter.transport.export_called)

    def setUp(self):
        self._handlers_cache = logging.getLogger().handlers[:]

    def tearDown(self):
        # cleanup handlers
        logging.getLogger().handlers = self._handlers_cache[:]


class MockTransport(object):
    def __init__(self):
        self.export_called = False

    def export(self, trace):
        self.export_called = True


class _Handler(object):
    def __init__(self, level):
        self.level = level

    def acquire(self):
        pass  # pragma: NO COVER

    def release(self):
        pass  # pragma: NO COVER
