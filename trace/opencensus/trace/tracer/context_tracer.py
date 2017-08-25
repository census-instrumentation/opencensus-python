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

from opencensus.trace.propagation import google_cloud_format
from opencensus.trace.reporters import print_reporter
from opencensus.trace.samplers.always_on import AlwaysOnSampler
from opencensus.trace.span_context import SpanContext
from opencensus.trace.trace import Trace
from opencensus.trace import labels_helper
from opencensus.trace import trace_span


class ContextTracer(object):
    """The interface for tracing a request context.

    :type span_context: :class:`~opencensus.trace.span_context.SpanContext`
    :param span_context: SpanContext encapsulates the current context within
                         the request's trace.

    :type sampler: :class:`type`
    :param sampler: Class for creating new Sampler objects. It should extend
                    from the base :class:`.Sampler` type and implement
                    :meth:`.Sampler.should_sample`. Defaults to
                    :class:`.AlwaysOnSampler`. The rest options are
                    :class:`.AlwaysOffSampler`, :class:`.FixedRateSampler`.

    :type reporter: :class:`type`
    :param reporter: Class for creating new Reporter objects. Default to
                     :class:`.PrintReporter`. The rest option is
                     :class:`.FileReporter`.
    """
    def __init__(
            self,
            span_context=None,
            sampler=None,
            reporter=None,
            propagator=None):
        if span_context is None:
            span_context = SpanContext()

        if sampler is None:
            sampler = AlwaysOnSampler()

        if reporter is None:
            reporter = print_reporter.PrintReporter()

        if propagator is None:
            propagator = google_cloud_format.GoogleCloudFormatPropagator()

        self.span_context = span_context
        self.sampler = sampler
        self.reporter = reporter
        self.propagator = propagator
        self.trace_id = span_context.trace_id
        self.enabled = self.set_enabled()
        self.cur_trace = self.trace()
        self._span_stack = []
        self.root_span_id = span_context.span_id

    def set_enabled(self):
        """Determine whether to sample this request or not.
        If the context forces not tracing, just set enabled to False.
        Else follow the sampler.

        :rtype: bool
        :returns: Whether to trace the request or not.
        """
        if self.span_context.enabled is False:
            return False
        elif self.sampler.should_sample is True:
            return True
        else:
            return False

    def trace_decorator(self):
        """Decorator to trace a function."""

        def decorator(func):

            def wrapper(*args, **kwargs):
                self.start_span(name=func.__name__)
                return_value = func(*args, **kwargs)
                self.end_span()
                return return_value

            return wrapper

        return decorator

    def trace(self):
        """Create a trace using the context information.

        :rtype: :class:`~opencensus.trace.trace.Trace`
        :returns: The Trace object.
        """
        if self.enabled is True:
            return Trace(trace_id=self.trace_id)
        else:
            return NullObject()

    def start_trace(self):
        """Start a trace."""
        if self.enabled is False:
            return

        self.cur_trace.start()

    def end_trace(self):
        """End a trace."""
        if self.enabled is False:
            return

        # Insert the common labels to spans
        helper = labels_helper.LabelsHelper(self)
        helper.set_labels()

        # Send the traces when finish
        trace = self.get_trace_json()

        if trace is not None:
            self.reporter.report(trace)

        self.cur_trace.finish()

    def span(self, name='span'):
        """Create a new span with the trace using the context information.

        :type name: str
        :param name: The name of the span.

        :rtype: :class:`~opencensus.trace.trace_span.TraceSpan`
        :returns: The TraceSpan object.
        """
        if self.enabled is False:
            return NullObject()

        span = self.start_span(name=name)
        return span

    def start_span(self, name='span'):
        """Start a span.

        :type name: str
        :param name: The name of the span.

        :rtype: :class:`~opencensus.trace.trace_span.TraceSpan`
        :returns: The TraceSpan object.
        """
        if self.enabled is True:
            parent_span_id = self.span_context.span_id
            span = trace_span.TraceSpan(
                name,
                parent_span_id=parent_span_id,
                context_tracer=self)
            self.cur_trace.spans.append(span)
            self._span_stack.append(span)
            self.span_context.span_id = span.span_id
            span.start()
            return span
        else:
            return NullObject()

    def end_span(self):
        """End a span. Remove the span from the span stack, and update the
        span_id in TraceContext as the current span_id which is the peek
        element in the span stack.
        """
        if self.enabled is False:
            return

        try:
            cur_span = self._span_stack.pop()
        except IndexError:
            logging.error('No span is active, cannot end any span.')
            raise

        cur_span.finish()

        if not self._span_stack:
            self.span_context.span_id = self.root_span_id
        else:
            self.span_context.span_id = self._span_stack[-1].span_id

    def list_collected_spans(self):
        return self.cur_trace.spans

    def add_label_to_spans(self, label_key, label_value):
        """Add label to the spans in current trace.

        :type label_key: str
        :param label_key: Label key.

        :type label_value:str
        :param label_value: Label value.
        """
        for span in self.cur_trace.spans:
            span.add_label(label_key, label_value)

    def get_trace_json(self):
        """Get the JSON format trace."""
        spans_list = []
        for root_span in self.cur_trace.spans:
            span_tree = list(iter(root_span))
            span_tree_json = [trace_span.format_span_json(span)
                              for span in span_tree]
            spans_list.extend(span_tree_json)

        if len(spans_list) == 0:
            return

        trace = {
            'traceId': self.cur_trace.trace_id,
            'spans': spans_list,
        }

        return trace


class NullObject(object):
    """Empty object as a helper for faking Trace and TraceSpan when tracing is
    disabled.
    """
    def __enter__(self):
        pass  # pragma: NO COVER

    def __exit__(self, exc_type, exc_value, traceback):
        pass  # pragma: NO COVER
