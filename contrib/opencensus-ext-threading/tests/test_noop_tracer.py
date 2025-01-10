import unittest
from unittest.mock import patch, MagicMock

from opencensus.trace.tracers.noop_tracer import NoopTracer
from opencensus.ext.threading.trace import wrap_submit, wrap_apply_async


class TestNoopTracer(unittest.TestCase):
    """
    In case no OpenCensus context is present (i.e. we have a NoopTracer), do _not_ pass down tracer in apply_async
    and submit; instead invoke function directly.
    """

    @patch("opencensus.ext.threading.trace.wrap_task_func")
    @patch("opencensus.trace.execution_context.get_opencensus_tracer")
    def test_noop_tracer_apply_async(
        self, get_opencensus_tracer_mock: MagicMock, wrap_task_func_mock: MagicMock
    ):
        mock_tracer = NoopTracer()
        get_opencensus_tracer_mock.return_value = mock_tracer
        submission_function_mock = MagicMock()
        original_function_mock = MagicMock()

        wrap_apply_async(submission_function_mock)(None, original_function_mock)

        # check whether invocation of original function _has_ happened
        submission_function_mock.assert_called_once_with(
            None, original_function_mock, args=(), kwds={}
        )

        # ensure that the function has _not_ been wrapped
        wrap_task_func_mock.assert_not_called()

    @patch("opencensus.ext.threading.trace.wrap_task_func")
    @patch("opencensus.trace.execution_context.get_opencensus_tracer")
    def test_noop_tracer_wrap_submit(
        self, get_opencensus_tracer_mock: MagicMock, wrap_task_func_mock: MagicMock
    ):
        mock_tracer = NoopTracer()
        get_opencensus_tracer_mock.return_value = mock_tracer
        submission_function_mock = MagicMock()
        original_function_mock = MagicMock()

        wrap_submit(submission_function_mock)(None, original_function_mock)

        # check whether invocation of original function _has_ happened
        submission_function_mock.assert_called_once_with(None, original_function_mock)

        # ensure that the function has _not_ been wrapped
        wrap_task_func_mock.assert_not_called()
