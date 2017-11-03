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

from opencensus.trace import execution_context
from opencensus.trace.span_context import SpanContext
from opencensus.trace import span as trace_span
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
        self.root_span_id = span_context.span_id

        # List of spans to report
        self._spans_list = []

    def finish(self):
        """Finish all spans

        :rtype: dict
        :returns: JSON format trace.
        """
        trace = self._get_trace_json()
        self._spans_list = []

        return trace

    def span(self, name='span'):
        """Create a new span with the trace using the context information.

        :type name: str
        :param name: The name of the span.

        :rtype: :class:`~opencensus.trace.span.Span`
        :returns: The Span object.
        """
        span = self.start_span(name=name)
        return span

    def start_span(self, name='span'):
        """Start a span.

        :type name: str
        :param name: The name of the span.

        :rtype: :class:`~opencensus.trace.span.Span`
        :returns: The Span object.
        """
        parent_span = self.current_span()

        # If a span has remote parent span, then the parent_span.span_id
        # should be the span_id from the request header.
        if parent_span is None:
            parent_span = base.NullContextManager(
                span_id=self.span_context.span_id)

        span = trace_span.Span(
            name,
            parent_span=parent_span,
            context_tracer=self)
        self._spans_list.append(span)
        self.span_context.span_id = span.span_id
        execution_context.set_current_span(span)
        span.start()
        return span

    def end_span(self):
        """End a span. Remove the span from the span stack, and update the
        span_id in TraceContext as the current span_id which is the peek
        element in the span stack.
        """
        cur_span = self.current_span()

        if cur_span is None:
            logging.warning('No active span, cannot do end_span.')
            return

        cur_span.finish()
        self.span_context.span_id = cur_span.parent_span.span_id

        if isinstance(cur_span.parent_span, trace_span.Span):
            execution_context.set_current_span(cur_span.parent_span)
        else:
            execution_context.set_current_span(None)

    def current_span(self):
        """Return the current span."""
        current_span = execution_context.get_current_span()

        return current_span

    def list_collected_spans(self):
        return self._spans_list

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
        for span in self._spans_list:
            span.add_label(label_key, label_value)

    def _get_trace_json(self):
        """Get the JSON format trace."""
        spans_list = []
        for root_span in self._spans_list:
            span_tree = list(iter(root_span))
            span_tree_json = [trace_span.format_span_json(span)
                              for span in span_tree]
            spans_list.extend(span_tree_json)

        if len(spans_list) == 0:
            return

        trace = {
            'traceId': self.trace_id,
            'spans': spans_list,
        }

        return trace
