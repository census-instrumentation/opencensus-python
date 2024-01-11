import unittest
from unittest.mock import patch, MagicMock
from opencensus.ext.threading.trace import wrap_submit, wrap_apply_async


class TestTracer(unittest.TestCase):
    """
    Ensures that sampler, exporter, propagator are passed through
    in case global tracer is present.
    """

    @patch("opencensus.trace.propagation.binary_format.BinaryFormatPropagator")
    @patch("opencensus.ext.threading.trace.wrap_task_func")
    @patch("opencensus.trace.execution_context.get_opencensus_tracer")
    def test_apply_async_context_passed(
        self,
        get_opencensus_tracer_mock: MagicMock,
        wrap_task_func_mock: MagicMock,
        binary_format_propagator_mock: MagicMock,
    ):
        mock_tracer = NoNoopTracerMock()
        # ensure that unique object is generated
        mock_tracer.sampler = MagicMock()
        mock_tracer.exporter = MagicMock()
        mock_tracer.propagator = MagicMock()

        get_opencensus_tracer_mock.return_value = mock_tracer

        submission_function_mock = MagicMock()
        original_function_mock = MagicMock()

        wrap_apply_async(submission_function_mock)(None, original_function_mock)

        # check whether invocation of original function _has_ happened
        call = submission_function_mock.call_args_list[0].kwargs

        self.assertEqual(id(call["kwds"]["sampler"]), id(mock_tracer.sampler))
        self.assertEqual(id(call["kwds"]["exporter"]), id(mock_tracer.exporter))
        self.assertEqual(id(call["kwds"]["propagator"]), id(mock_tracer.propagator))

    @patch("opencensus.trace.propagation.binary_format.BinaryFormatPropagator")
    @patch("opencensus.ext.threading.trace.wrap_task_func")
    @patch("opencensus.trace.execution_context.get_opencensus_tracer")
    def test_wrap_submit_context_passed(
        self,
        get_opencensus_tracer_mock: MagicMock,
        wrap_task_func_mock: MagicMock,
        binary_format_propagator_mock: MagicMock,
    ):
        mock_tracer = NoNoopTracerMock()
        # ensure that unique object is generated
        mock_tracer.sampler = MagicMock()
        mock_tracer.exporter = MagicMock()
        mock_tracer.propagator = MagicMock()

        get_opencensus_tracer_mock.return_value = mock_tracer

        submission_function_mock = MagicMock()
        original_function_mock = MagicMock()

        wrap_submit(submission_function_mock)(None, original_function_mock)

        # check whether invocation of original function _has_ happened
        call = submission_function_mock.call_args_list[0].kwargs

        self.assertEqual(id(call["sampler"]), id(mock_tracer.sampler))
        self.assertEqual(id(call["exporter"]), id(mock_tracer.exporter))
        self.assertEqual(id(call["propagator"]), id(mock_tracer.propagator))


class NoNoopTracerMock(MagicMock):
    pass
