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

import sys
from contextlib import contextmanager
import logging

from opencensus import log

if sys.version_info < (3,):
    import unittest2 as unittest
    import mock
else:
    import unittest
    from unittest import mock


@contextmanager
def mock_context(context=None):
    """Mock the OC execution context globally."""
    if context is None:
        context = mock.Mock()
    with mock.patch("opencensus.trace.execution_context", context):
        # We have to mock log explicitly since it imports execution_context
        # before we can patch it
        with mock.patch("opencensus.log.execution_context", context):
            yield context


@contextmanager
def mock_tracer(trace_id=None, span_id=None, sampling_decision=None):
    """Mock the OC execution context to return a mock tracer.

    Mocks `opencensus.trace.execution_context` so that `get_opencensus_tracer`
    returns a dummy tracer with a fixed trace ID, span ID, and sampling
    decision and yields the tracer.
    """
    tracer = mock.Mock()
    tracer.span_context.trace_id = trace_id
    tracer.span_context.span_id = span_id
    tracer.span_context.trace_options.get_enabled = sampling_decision

    with mock_context() as mock_ec:
        mock_ec.get_opencensus_tracer.return_value = tracer
        yield tracer


def get_logger_names():
    return set(logging.Logger.manager.loggerDict.keys())


def delete_loggers(logger_names):
    for ln in logger_names:
        try:
            del logging.Logger.manager.loggerDict[ln]
        except KeyError:
            pass


class TestLogger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._old_logger_names = get_logger_names()

    def tearDown(self):
        delete_loggers(get_logger_names() - self._old_logger_names)

    def test_no_import_effects(self):
        """Check that importing OC logging doesn't affect logging defaults."""
        with mock_tracer():
            logger = logging.getLogger('a.b.c')

            self.assertIsInstance(logger, logging.Logger)
            self.assertNotIsInstance(logger, log.TraceLogger)

            with self.assertLogs('a.b.c', level=logging.INFO):
                logger.info("test message")

            self.assertListEqual(log.execution_context.mock_calls, [])
            log.execution_context.get_opencensus_tracer.assert_not_called()


class TestTraceLogger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._old_logger_names = get_logger_names()
        cls._old_logger_class = logging.getLoggerClass()
        log.use_oc_logging()

    @classmethod
    def tearDownClass(cls):
        logging.setLoggerClass(cls._old_logger_class)

    def tearDown(self):
        delete_loggers(get_logger_names() - self._old_logger_names)

    def test_logger_unused(self):
        """Check that we don't touch the OC context until log time."""
        with mock_tracer():
            logger = logging.getLogger('a.b.c')
            self.assertIsInstance(logger, log.TraceLogger)
            self.assertListEqual(log.execution_context.mock_calls, [])
            log.execution_context.get_opencensus_tracer.assert_not_called()

    def test_logrecord_attrs(self):
        """Check that OC attrs are available to handlers."""
        with mock_tracer("trace_id", "span_id", True):
            logger = logging.getLogger('a.b.c')

            with self.assertLogs('a.b.c', level=logging.INFO) as cm:
                logger.info("test message")

        self.assertEqual(len(cm.records), 1)
        [record] = cm.records
        self.assertEqual(record.traceId, "trace_id")
        self.assertEqual(record.spanId, "span_id")
        self.assertEqual(record.traceSampled, True)
        self.assertEqual(record.message, "test message")

    def test_logrecord_extra(self):
        """Check that extra attrs override defaults."""
        with mock_tracer("trace_id", "span_id", True):
            logger = logging.getLogger('a.b.c')

            with self.assertLogs('a.b.c', level=logging.INFO) as cm:
                logger.info(
                    "test message",
                    extra={
                        'otherKey': "other val",
                        'traceId': "override"
                    })

        self.assertEqual(len(cm.records), 1)
        [record] = cm.records
        self.assertEqual(record.otherKey, "other val")
        self.assertEqual(record.traceId, "override")
        self.assertEqual(record.spanId, "span_id")
        self.assertEqual(record.traceSampled, True)
        self.assertEqual(record.message, "test message")

    def test_exc_info(self):
        """Check that we don't interfere with exception handling."""
        with mock_tracer():
            logger = logging.getLogger('ex_logger')
            with self.assertLogs('ex_logger', level=logging.ERROR) as cm:
                try:
                    raise ValueError
                except ValueError:
                    logger.exception("uh oh")

        self.assertEqual(len(cm.records), 1)
        [record] = cm.records
        self.assertIsNotNone(record.exc_info)
        ex_type, ex_value, tb = record.exc_info
        self.assertEqual(ex_type, ValueError)
        self.assertIsInstance(ex_value, ValueError)
        self.assertIsNotNone(tb)

    def test_logrecord_defaults(self):
        """Check defaults when tracer is null or raises."""
        with mock_context() as mec1:
            mec1.get_opencensus_tracer.return_value = None
            logger = logging.getLogger('tracer_null')

            with self.assertLogs('tracer_null', level=logging.INFO) as cm1:
                with self.assertLogs(log._meta_logger, level=logging.ERROR):
                    logger.info("test message")

        self.assertEqual(len(cm1.records), 1)
        [r1] = cm1.records
        self.assertEqual(r1.traceId, log.ATTR_DEFAULTS.trace_id)
        self.assertEqual(r1.spanId, log.ATTR_DEFAULTS.span_id)
        self.assertEqual(r1.traceSampled, log.ATTR_DEFAULTS.sampling_decision)

        with mock_context() as mec2:
            mec2.get_opencensus_tracer.side_effect = ValueError
            logger = logging.getLogger('tracer_error')

            with self.assertLogs('tracer_error', level=logging.INFO) as cm2:
                with self.assertLogs(log._meta_logger, level=logging.ERROR):
                    logger.info("test message")

        self.assertEqual(len(cm2.records), 1)
        [r2] = cm2.records
        self.assertEqual(r2.traceId, log.ATTR_DEFAULTS.trace_id)
        self.assertEqual(r2.spanId, log.ATTR_DEFAULTS.span_id)
        self.assertEqual(r2.traceSampled, log.ATTR_DEFAULTS.sampling_decision)

    def test_default_trace_id(self):
        """Check defaults when trace ID is null or raises."""
        with mock_tracer(None, "span_id", True):
            logger = logging.getLogger('trace_id_null')

            with self.assertLogs('trace_id_null', level=logging.INFO) as cm2:
                logger.info("test message")

        with mock_tracer(span_id='span_id', sampling_decision=True) as mt:
            type(mt.span_context).trace_id = mock.PropertyMock(
                side_effect=ValueError)
            logger = logging.getLogger('trace_id_error')

            with self.assertLogs('trace_id_error', level=logging.INFO) as cm2:
                with self.assertLogs(log._meta_logger, level=logging.ERROR):
                    logger.info("test message")

        self.assertEqual(len(cm2.records), 1)
        [record] = cm2.records
        self.assertEqual(record.traceId, log.ATTR_DEFAULTS.trace_id)
        self.assertEqual(record.spanId, "span_id")
        self.assertEqual(record.traceSampled, True)

    def test_default_span_id(self):
        """Check defaults when span ID is null or raises."""
        with mock_tracer("trace_id", None, True):
            logger = logging.getLogger('span_id_null')
            with self.assertLogs('span_id_null', level=logging.INFO) as cm1:
                logger.info("test message")

        self.assertEqual(len(cm1.records), 1)
        [r1] = cm1.records
        self.assertEqual(r1.traceId, "trace_id")
        self.assertEqual(r1.spanId, log.ATTR_DEFAULTS.span_id)
        self.assertEqual(r1.traceSampled, True)

        with mock_tracer(trace_id="trace_id", sampling_decision=True) as mt:
            type(mt.span_context).span_id = mock.PropertyMock(
                side_effect=ValueError)
            logger = logging.getLogger('span_id_error')

            with self.assertLogs('span_id_error', level=logging.INFO) as cm2:
                with self.assertLogs(log._meta_logger, level=logging.ERROR):
                    logger.info("test message")

        self.assertEqual(len(cm2.records), 1)
        [r2] = cm2.records
        self.assertEqual(r2.traceId, "trace_id")
        self.assertEqual(r2.spanId, log.ATTR_DEFAULTS.span_id)
        self.assertEqual(r2.traceSampled, True)

    def test_default_sampling_decision(self):
        """Check defaults when sampling decision is null or raises."""
        with mock_tracer("trace_id", "span_id", None):
            logger = logging.getLogger('sd_null')
            with self.assertLogs('sd_null', level=logging.INFO) as cm1:
                logger.info("test message")

        self.assertEqual(len(cm1.records), 1)
        [r1] = cm1.records
        self.assertEqual(r1.traceId, "trace_id")
        self.assertEqual(r1.spanId, "span_id")
        self.assertEqual(r1.traceSampled, log.ATTR_DEFAULTS.sampling_decision)

        with mock_tracer(trace_id="trace_id", span_id="span_id") as mt2:
            mt2.span_context.trace_options = None
            logger = logging.getLogger('sd_missing')

            with self.assertLogs('sd_missing', level=logging.INFO) as cm2:
                logger.info("test message")

        self.assertEqual(len(cm2.records), 1)
        [r2] = cm2.records
        self.assertEqual(r2.traceId, "trace_id")
        self.assertEqual(r2.spanId, "span_id")
        self.assertEqual(r2.traceSampled, log.ATTR_DEFAULTS.sampling_decision)

        with mock_tracer(trace_id="trace_id", span_id="span_id") as mt3:
            type(mt3.span_context.trace_options).get_enabled =\
                 mock.PropertyMock(side_effect=ValueError)
            logger = logging.getLogger('sd_error')

            with self.assertLogs('sd_error', level=logging.INFO) as cm3:
                with self.assertLogs(log._meta_logger, level=logging.ERROR):
                    logger.info("test message")

        self.assertEqual(len(cm3.records), 1)
        [r3] = cm3.records
        self.assertEqual(r3.traceId, "trace_id")
        self.assertEqual(r3.spanId, "span_id")
        self.assertEqual(r3.traceSampled, log.ATTR_DEFAULTS.sampling_decision)


class TestTraceLoggingAdapter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._old_logger_names = get_logger_names()

    def tearDown(self):
        delete_loggers(get_logger_names() - self._old_logger_names)

    def test_adapter_lr_attrs(self):
        """Check that logging adapter adds OC attrs."""
        with mock_tracer("trace_id", "span_id", True):
            logger = logging.getLogger('a.b.c')
            adapted_logger = log.TraceLoggingAdapter(logger, {})

            with self.assertLogs('a.b.c', level=logging.INFO) as cm:
                adapted_logger.info("test message")

        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(len(cm.records), 1)
        [record] = cm.records
        self.assertEqual(record.traceId, "trace_id")
        self.assertEqual(record.spanId, "span_id")
        self.assertEqual(record.traceSampled, True)
        self.assertEqual(record.message, "test message")

    def test_adapter_extra(self):
        """Check that extra attrs override defaults."""
        with mock_tracer("trace_id", "span_id", True):
            logger = logging.getLogger('a.b.c')
            adapted_logger = log.TraceLoggingAdapter(logger, {
                'otherKey': "other val",
                'traceId': "override one"
            })

            with self.assertLogs('a.b.c', level=logging.INFO) as cm1:
                adapted_logger.info("test message")

            with self.assertLogs('a.b.c', level=logging.INFO) as cm2:
                adapted_logger.info(
                    "test message",
                    extra={
                        'anotherKey': "other val",
                        'traceId': "override two"
                    })

        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(len(cm1.records), 1)
        [r1] = cm1.records
        self.assertEqual(r1.otherKey, "other val")
        self.assertEqual(r1.traceId, "override one")
        self.assertEqual(r1.spanId, "span_id")
        self.assertEqual(r1.traceSampled, True)
        self.assertEqual(r1.message, "test message")

        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(len(cm2.records), 1)
        [r2] = cm2.records
        self.assertEqual(r2.traceId, "override two")
        self.assertEqual(r2.spanId, "span_id")
        self.assertEqual(r2.traceSampled, True)
        self.assertEqual(r2.message, "test message")
