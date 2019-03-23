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

from opencensus.trace import logging_exporter
from opencensus.trace import span_context
from opencensus.trace import span_data as span_data_module


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

        span_datas = [
            span_data_module.SpanData(
                name='span',
                context=span_context.SpanContext(trace_id='1'),
                span_id='1111',
                parent_span_id=None,
                attributes=None,
                start_time=None,
                end_time=None,
                child_span_count=None,
                stack_trace=None,
                time_events=None,
                links=None,
                status=None,
                same_process_as_parent_span=None,
                span_kind=0,
            )
        ]
        exporter.emit(span_datas)

        logger.info.assert_called_once_with(
            span_data_module.format_legacy_trace_json(span_datas)
        )

    def test_export(self):
        exporter = logging_exporter.LoggingExporter(transport=MockTransport)
        exporter.export({})

        self.assertTrue(exporter.transport.export_called)

    def setUp(self):
        self._handlers_cache = logging.getLogger().handlers[:]

    def tearDown(self):
        # cleanup handlers
        logging.getLogger().handlers = self._handlers_cache[:]


class MockTransport(object):
    def __init__(self, exporter=None):
        self.export_called = False
        self.exporter = exporter

    def export(self, trace):
        self.export_called = True


class _Handler(object):
    def __init__(self, level):
        self.level = level

    def acquire(self):
        pass  # pragma: NO COVER

    def release(self):
        pass  # pragma: NO COVER
