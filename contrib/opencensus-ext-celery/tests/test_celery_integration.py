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

import unittest

import mock

from opencensus.ext.celery.trace import (
    CELERY_METADATA_THREAD_LOCAL_KEY,
    SPAN_THREAD_LOCAL_KEY,
    TRACING_HEADER_NAME,
    CeleryMetaWrapper,
    after_task_publish_handler,
    before_task_publish_handler,
    task_failure_handler,
    task_prerun_handler,
    task_success_handler,
    trace_integration,
    tracing_settings,
)
from opencensus.trace import execution_context, print_exporter, samplers
from opencensus.trace import tracer as tracer_module
from opencensus.trace.propagation import trace_context_http_header_format


class TestCeleryIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        execution_context.clear()
        cls.propagator = \
            trace_context_http_header_format.TraceContextPropagator()
        cls.exporter = print_exporter.PrintExporter()
        cls.sampler = samplers.ProbabilitySampler()

    def tearDown(self):
        execution_context.clear()

    def test_configuration(self):
        tracer = tracer_module.Tracer(
            sampler=self.sampler,
            exporter=self.exporter,
            propagator=self.propagator)
        trace_integration(tracer)

        assert tracing_settings.get('propagator') == self.propagator
        assert tracing_settings.get('sampler') == self.sampler
        assert tracing_settings.get('exporter') == self.exporter

    def test_before_task_publish_handler(self):
        (tracer, span_context, trace_metadata, trace_id,
         span_id) = self.prepare_test()

        assert self.propagator.to_headers(span_context) == trace_metadata

        headers = {}
        before_task_publish_handler(headers)

        span_context = self.propagator.from_headers(
            headers[TRACING_HEADER_NAME]
        )

        assert span_context.trace_id == trace_id
        assert span_context.span_id != span_id

    @mock.patch('opencensus.ext.celery.trace.log')
    def test_before_task_publish_handler_error(self, mock_logger):
        execution_context.set_opencensus_tracer(None)
        headers = {}

        with mock_logger:
            before_task_publish_handler(headers)

        mock_logger.error.assert_called_once()

    def test_after_task_publish_handler(self):
        (tracer, span_context, trace_metadata, trace_id,
         span_id) = self.prepare_test()

        tracer.start_span()

        assert tracer.current_span() is not None

        after_task_publish_handler()

        assert tracer.current_span() is None

    @mock.patch('opencensus.ext.celery.trace.log')
    def test_after_task_publish_handler_error(self, mock_logger):
        execution_context.set_opencensus_tracer(None)

        with mock_logger:
            after_task_publish_handler()

        mock_logger.error.assert_called_once()

    def test_task_prerun_handler(self):
        (tracer, span_context, trace_metadata, trace_id,
         span_id) = self.prepare_test()

        task = Task()
        task.request = Request()

        setattr(task.request, TRACING_HEADER_NAME, trace_metadata)

        sender = Sender()
        sender.name = 'sender_name'

        task_prerun_handler(task=task, sender=sender)

        span = execution_context.get_opencensus_attr(SPAN_THREAD_LOCAL_KEY)

        assert span is not None
        assert span.name == 'celery.consume.sender_name'

    @mock.patch('opencensus.ext.celery.trace.log')
    def test_task_prerun_handler_error(self, mock_logger):
        task = Task()
        task.request = Request()

        setattr(task.request, TRACING_HEADER_NAME, self.get_metadata())

        sender = Sender()
        sender.name = 'sender_name'

        with mock_logger:
            task_prerun_handler(task=task, sender=sender)

        mock_logger.error.assert_called_once()

    def test_task_success_handler(self):
        (tracer, span_context, trace_metadata, trace_id,
         span_id) = self.prepare_test()

        span = tracer.start_span()
        execution_context.set_opencensus_attr(
            SPAN_THREAD_LOCAL_KEY, span)

        task_success_handler()

        span = execution_context.get_opencensus_attr(SPAN_THREAD_LOCAL_KEY)

        assert span is not None
        assert span.attributes['result'] == 'success'

    @mock.patch('opencensus.ext.celery.trace.log')
    def test_task_success_handler_error(self, mock_logger):
        self.prepare_test()

        execution_context.set_opencensus_attr(
            SPAN_THREAD_LOCAL_KEY, None)

        with mock_logger:
            task_success_handler()

        mock_logger.error.assert_called_once()

    @mock.patch('opencensus.ext.celery.trace.log')
    def test_task_failure_handler(self, mock_logger): # noqa mock_logger
        (tracer, span_context, trace_metadata, trace_id,
         span_id) = self.prepare_test()

        span = tracer.start_span()
        execution_context.set_opencensus_attr(
            SPAN_THREAD_LOCAL_KEY, span)

        task_failure_handler(traceback='traceback')

        span = execution_context.get_opencensus_attr(SPAN_THREAD_LOCAL_KEY)

        assert span is not None
        assert span.attributes['stacktrace'] == 'traceback'

    @mock.patch('opencensus.ext.celery.trace.log')
    def test_task_failure_handler_error(self, mock_logger):
        execution_context.set_opencensus_attr(
            SPAN_THREAD_LOCAL_KEY, None)

        with mock_logger:
            task_failure_handler(traceback='traceback')

        mock_logger.error.assert_called_once()

    def test_get_celery_meta(self):
        trace_metadata, trace_id, span_id = self.get_metadata()

        execution_context.set_opencensus_attr(
            CELERY_METADATA_THREAD_LOCAL_KEY,
            trace_metadata)

        span_context = self.propagator.from_headers(
            CeleryMetaWrapper(None))

        assert span_context.trace_id == trace_id
        assert span_context.span_id == span_id

    def prepare_test(self):

        trace_metadata, trace_id, span_id = self.get_metadata()

        span_context = self.propagator.from_headers(
            CeleryMetaWrapper(trace_metadata))

        # Reload the tracer with the new span context
        tracer = tracer_module.Tracer(
            span_context=span_context,
            sampler=self.sampler,
            exporter=self.exporter,
            propagator=self.propagator)

        execution_context.set_opencensus_tracer(tracer)

        trace_integration(tracer)

        return tracer, span_context, trace_metadata, trace_id, span_id

    @staticmethod
    def get_metadata():
        trace_id = '1dd43a2d6b2549c6bc2a1a54c2fc0b04'
        span_id = '6e0c63257de34c92'
        traceparent = '00-{}-{}-01'.format(trace_id, span_id)

        return {
            'traceparent': traceparent
        }, trace_id, span_id


class Task:
    pass


class Request:
    pass


class Sender:
    pass
