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

from opencensus.trace.span_context import SpanContext
from opencensus.trace import labels_helper
from opencensus.trace import trace_span
from opencensus.trace.trace import Trace
from opencensus.trace.tracer import base


class ContextTracer(base.Tracer):
    """The interface for tracing a request context.

    :type span_context: :class:`~opencensus.trace.span_context.SpanContext`
    :param span_context: SpanContext encapsulates the current context within
                         the request's trace.
    """
    def __init__(self, span_context=None):
        if span_context is None:
            span_context = SpanContext()

        self.span_context = span_context
        self.trace_id = span_context.trace_id
        self.cur_trace = self.trace()
        self._span_stack = []
        self.root_span_id = span_context.span_id

    def trace(self):
        """Create a trace using the context information.

        :rtype: :class:`~opencensus.trace.trace.Trace`
        :returns: The Trace object.
        """
        return Trace(trace_id=self.trace_id)

    def start_trace(self):
        """Start a trace."""
        self.cur_trace.start()

    def end_trace(self):
        """End a trace.

        :rtype: dict
        :returns: JSON format trace.
        """
        # Insert the common labels to spans
        helper = labels_helper.LabelsHelper(self)
        helper.set_labels()

        trace = self._get_trace_json()
        self.cur_trace.finish()

        return trace

    def span(self, name='span'):
        """Create a new span with the trace using the context information.

        :type name: str
        :param name: The name of the span.

        :rtype: :class:`~opencensus.trace.trace_span.TraceSpan`
        :returns: The TraceSpan object.
        """
        span = self.start_span(name=name)
        return span

    def start_span(self, name='span'):
        """Start a span.

        :type name: str
        :param name: The name of the span.

        :rtype: :class:`~opencensus.trace.trace_span.TraceSpan`
        :returns: The TraceSpan object.
        """
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

    def end_span(self):
        """End a span. Remove the span from the span stack, and update the
        span_id in TraceContext as the current span_id which is the peek
        element in the span stack.
        """
        cur_span = self.current_span()

        self._span_stack.pop()
        cur_span.finish()

        if not self._span_stack:
            self.span_context.span_id = self.root_span_id
        else:
            self.span_context.span_id = self._span_stack[-1].span_id

    def current_span(self):
        """Return the current span."""
        try:
            cur_span = self._span_stack[-1]
        except IndexError:
            logging.error('No span in the span stack.')
            cur_span = base.NullContextManager()

        return cur_span

    def list_collected_spans(self):
        return self.cur_trace.spans

    def add_label_to_current_span(self, label_key, label_value):
        """Add label to current span.

        :type label_key: str
        :param label_key: Label key.

        :type label_value:str
        :param label_value: Label value.
        """
        current_span = self.current_span()
        current_span.add_label(label_key, label_value)

    def add_label_to_spans(self, label_key, label_value):
        """Add label to the spans in current trace.

        :type label_key: str
        :param label_key: Label key.

        :type label_value:str
        :param label_value: Label value.
        """
        for span in self.cur_trace.spans:
            span.add_label(label_key, label_value)

    def _get_trace_json(self):
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
