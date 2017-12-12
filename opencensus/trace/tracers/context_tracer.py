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
from opencensus.trace.exporters import print_exporter
from opencensus.trace.tracers import base


class ContextTracer(base.Tracer):
    """The interface for tracing a request context.

    :type span_context: :class:`~opencensus.trace.span_context.SpanContext`
    :param span_context: SpanContext encapsulates the current context within
                         the request's trace.
    """
    def __init__(self, exporter=None, span_context=None):
        if exporter is None:
            exporter = print_exporter.PrintExporter()

        if span_context is None:
            span_context = SpanContext()

        self.exporter = exporter
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
        self._spans_list = []

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

    def end_span(self, *args, **kwargs):
        """End a span. Update the span_id in SpanContext to the current span's
        parent span id; Update the current span.
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

        span_json = self.get_trace_json(cur_span)
        self.exporter.export(span_json)

        return cur_span

    def current_span(self):
        """Return the current span."""
        current_span = execution_context.get_current_span()

        return current_span

    def list_collected_spans(self):
        return self._spans_list

    def add_attribute_to_current_span(self, attribute_key, attribute_value):
        """Add attribute to current span.

        :type attribute_key: str
        :param attribute_key: Attribute key.

        :type attribute_value:str
        :param attribute_value: Attribute value.
        """
        current_span = self.current_span()
        current_span.add_attribute(attribute_key, attribute_value)

    def get_trace_json(self, span):
        """Get the JSON format trace."""
        span_tree = list(iter(span))
        span_tree_list = [trace_span.format_span_json(span)
                          for span in span_tree]

        trace = {
            'traceId': self.trace_id,
            'spans': span_tree_list,
        }

        return trace
