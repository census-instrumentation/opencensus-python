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

from datetime import datetime
from itertools import chain

from opencensus.trace.enums import Enum
from opencensus.trace.span_context import generate_span_id
from opencensus.trace.tracer import base


class Span(object):
    """A span is an individual timed event which forms a node of the trace
    tree. Each span has its name, span id and parent id. The parent id
    indicates the causal relationships between the individual spans in a
    single distributed trace. Span that does not have a parent id is called
    root span. All spans associated with a specific trace also share a common
    trace id. Spans do not need to be continuous, there can be gaps between
    two spans.

    :type name: str
    :param name: The name of the span.

    :type kind: :class:`~opencensus.trace.enums.Enums.SpanKind`
    :param kind: Distinguishes between spans generated in a particular context.
                 For example, two spans with the same name may be
                 distinguished using RPC_CLIENT and RPC_SERVER to identify
                 queueing latency associated with the span.

    :type parent_span: :class:`~opencensus.trace.span.Span`
    :param parent_span: (Optional) Parent span.

    :type attributes: dict
    :param attributes: Collection of attributes associated with the span.
                   Attribute keys must be less than 128 bytes.
                   Attribute values must be less than 16 kilobytes.

    :type start_time: str
    :param start_time: (Optional) Start of the time interval (inclusive)
                       during which the trace data was collected from the
                       application.

    :type end_time: str
    :param end_time: (Optional) End of the time interval (inclusive) during
                     which the trace data was collected from the application.

    :type span_id: int
    :param span_id: Identifier for the span, unique within a trace.

    :type context_tracer: :class:`~opencensus.trace.tracer.context_tracer.
                                 ContextTracer`
    :param context_tracer: The tracer that holds a stack of spans. If this is
                           not None, then when exiting a span, use the end_span
                           method in the tracer class to finish a span. If no
                           tracer is passed in, then just finish the span using
                           the finish method in the Span class.
    """

    def __init__(
            self,
            name,
            kind=Enum.SpanKind.SPAN_KIND_UNSPECIFIED,
            parent_span=None,
            attributes=None,
            start_time=None,
            end_time=None,
            span_id=None,
            context_tracer=None):
        self.name = name
        self.kind = kind
        self.parent_span = parent_span
        self.start_time = start_time
        self.end_time = end_time

        if span_id is None:
            span_id = generate_span_id()

        if attributes is None:
            attributes = {}

        # Do not manipulate spans directly using the methods in Span Class,
        # make sure to use the RequestTracer.
        if parent_span is None:
            parent_span = base.NullContextManager()

        self.attributes = attributes
        self.span_id = span_id
        self._child_spans = []
        self.context_tracer = context_tracer

    @property
    def children(self):
        """The child spans of the current span."""
        return self._child_spans

    def span(self, name='child_span'):
        """Create a child span for the current span and append it to the child
        spans list.

        :type name: str
        :param name: (Optional) The name of the child span.

        :rtype: :class: `~opencensus.trace.span.Span`
        :returns: A child Span to be added to the current span.
        """
        child_span = Span(name, parent_span=self)
        self._child_spans.append(child_span)
        return child_span

    def add_attribute(self, attribute_key, attribute_value):
        """Add attribute to span.

        :type attribute_key: str
        :param attribute_key: Attribute key.

        :type attribute_value:str
        :param attribute_value: Attribute value.
        """
        self.attributes[attribute_key] = attribute_value

    def start(self):
        """Set the start time for a span."""
        self.start_time = datetime.utcnow().isoformat() + 'Z'

    def finish(self):
        """Set the end time for a span."""
        self.end_time = datetime.utcnow().isoformat() + 'Z'

    def __iter__(self):
        """Iterate through the span tree."""
        for span in chain(*(map(iter, self.children))):
            yield span
        yield self

    def __enter__(self):
        """Start a span."""
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Finish a span."""
        if self.context_tracer is not None:
            self.context_tracer.end_span()
            return

        self.finish()


def format_span_json(span):
    """Helper to format a Span in JSON format.

    :type span: :class:`~opencensus.trace.span.Span`
    :param span: A Span to be transferred to JSON format.

    :rtype: dict
    :returns: Formatted Span.
    """
    span_json = {
        'name': span.name,
        'kind': span.kind,
        'spanId': span.span_id,
        'startTime': span.start_time,
        'endTime': span.end_time,
    }

    parent_span_id = None

    if span.parent_span is not None:
        parent_span_id = span.parent_span.span_id

    if parent_span_id is not None:
        span_json['parentSpanId'] = parent_span_id

    if span.attributes is not None:
        span_json['attributes'] = span.attributes

    return span_json
