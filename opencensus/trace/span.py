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

from opencensus.trace import attributes
from opencensus.trace import link as link_module
from opencensus.trace import stack_trace
from opencensus.trace import status
from opencensus.trace import time_event as time_event_module
from opencensus.trace.span_context import generate_span_id
from opencensus.trace.tracers import base
from opencensus.trace.utils import _get_truncatable_str


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

    :type stack_trace: :class: `~opencensus.trace.stack_trace.StackTrace`
    :param stack_trace: (Optional) A call stack appearing in a trace

    :type time_events: list
    :param time_events: (Optional) A set of time events. You can have up to 32
                        annotations and 128 message events per span.

    :type links: list
    :param links: (Optional) Links associated with the span. You can have up
                  to 128 links per Span.

    :type status: :class: `~opencensus.trace.status.Status`
    :param status: (Optional) An optional final status for this span.

    :type same_process_as_parent_span: bool
    :param same_process_as_parent_span: (Optional) A highly recommended but not
                                        required flag that identifies when a
                                        trace crosses a process boundary.
                                        True when the parent_span belongs to
                                        the same process as the current span.

    :type context_tracer: :class:`~opencensus.trace.tracers.context_tracer.
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
            parent_span=None,
            attributes=None,
            start_time=None,
            end_time=None,
            span_id=None,
            stack_trace=None,
            time_events=None,
            links=None,
            status=None,
            same_process_as_parent_span=None,
            context_tracer=None):
        self.name = name
        self.parent_span = parent_span
        self.start_time = start_time
        self.end_time = end_time

        if span_id is None:
            span_id = generate_span_id()

        if attributes is None:
            attributes = {}

        # Do not manipulate spans directly using the methods in Span Class,
        # make sure to use the Tracer.
        if parent_span is None:
            parent_span = base.NullContextManager()

        if time_events is None:
            time_events = []

        if links is None:
            links = []

        self.attributes = attributes
        self.span_id = span_id
        self.stack_trace = stack_trace
        self.time_events = time_events
        self.links = links
        self.status = status
        self.same_process_as_parent_span = same_process_as_parent_span
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

    def add_time_event(self, time_event):
        """Add a TimeEvent.

        :type time_event: :class: `~opencensus.trace.time_event.TimeEvent`
        :param time_event: A TimeEvent object.
        """
        if isinstance(time_event, time_event_module.TimeEvent):
            self.time_events.append(time_event)
        else:
            raise TypeError("Type Error: received {}, but requires TimeEvent.".
                            format(type(time_event).__name__))

    def add_link(self, link):
        """Add a Link.

        :type link: :class: `~opencensus.trace.link.Link`
        :param link: A Link object.
        """
        if isinstance(link, link_module.Link):
            self.links.append(link)
        else:
            raise TypeError("Type Error: received {}, but requires Link.".
                            format(type(link).__name__))

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
        if traceback is not None:
            self.stack_trace = stack_trace.StackTrace.from_traceback(traceback)
        if exception_value is not None:
            self.status = status.Status.from_exception(exception_value)
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
        'displayName': _get_truncatable_str(span.name),
        'spanId': span.span_id,
        'startTime': span.start_time,
        'endTime': span.end_time,
        'childSpanCount': len(span._child_spans)
    }

    parent_span_id = None

    if span.parent_span is not None:
        parent_span_id = span.parent_span.span_id

    if parent_span_id is not None:
        span_json['parentSpanId'] = parent_span_id

    if span.attributes:
        span_json['attributes'] = attributes.Attributes(
            span.attributes).format_attributes_json()

    if span.stack_trace is not None:
        span_json['stackTrace'] = span.stack_trace.format_stack_trace_json()

    if span.time_events:
        span_json['timeEvents'] = {
            'timeEvent': [time_event.format_time_event_json()
                          for time_event in span.time_events]
        }

    if span.links:
        span_json['links'] = {
            'link': [
                link.format_link_json() for link in span.links]
        }

    if span.status is not None:
        span_json['status'] = span.status.format_status_json()

    if span.same_process_as_parent_span is not None:
        span_json['sameProcessAsParentSpan'] = \
            span.same_process_as_parent_span

    return span_json
