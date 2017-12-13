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

from opencensus.trace.tracers import base


class NoopTracer(base.Tracer):
    """No-op implementation of the :class:`Tracer` interface, all methods are
    no-ops. Should be used when tracing is not enabled or not sampled.
    """
    def finish(self):
        """End spans and send to reporter."""
        return None

    def span(self, name='span'):
        """Create a new span with the trace using the context information.

        :type name: str
        :param name: The name of the span.

        :rtype: :class:`~opencensus.trace.trace_span.Span`
        :returns: The Span object.
        """
        return base.NullContextManager()

    def start_span(self, name='span'):
        """Start a span.

        :type name: str
        :param name: The name of the span.

        :rtype: :class:`~opencensus.trace.trace_span.Span`
        :returns: The Span object.
        """
        return base.NullContextManager()

    def end_span(self):
        """End a span. Remove the span from the span stack, and update the
        span_id in TraceContext as the current span_id which is the peek
        element in the span stack.
        """
        return base.NullContextManager()

    def current_span(self):
        """Return the current span."""
        return base.NullContextManager()

    def add_attribute_to_current_span(self, attribute_key, attribute_value):
        """Add attribute to current span.

        :type attribute_key: str
        :param attribute_key: Attribute key.

        :type attribute_value:str
        :param attribute_value: Attribute value.
        """
        return

    def list_collected_spans(self):
        """List collected spans."""
        return None
