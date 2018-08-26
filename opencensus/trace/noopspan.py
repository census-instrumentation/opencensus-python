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
from opencensus.trace.span_context import generate_span_id
from opencensus.trace.tracers import base


class NoopSpan(object):
    """A NoopSpan is an individual timed event which forms a node of the trace
    tree. All operations are no-op.

    :type name: str
    :param name: The name of the span.

    :type parent_span: :class:`~opencensus.trace.noopspan.NoopSpan`
    :param parent_span: (Optional) Parent span.

    :type status: :class: `~opencensus.trace.status.Status`
    :param status: (Optional) An optional final status for this span.

    :type context_tracer: :class:`~opencensus.trace.tracers.noop_tracer.
                                 NoopTracer`
    :param context_tracer: The tracer that holds a stack of spans. If this is
                           not None, then when exiting a span, use the end_span
                           method in the tracer class to finish a span. If no
                           tracer is passed in, then just finish the span using
                           the finish method in the Span class.
    """

    def __init__(
            self,
            name=None,
            parent_span=None,
            status=None,
            context_tracer=None):
        self.name = name
        self.span_id = generate_span_id()
        self.parent_span = parent_span

        if parent_span is None:
            self.parent_span = base.NullContextManager()

        self.attributes = {}
        self.links = []
        self._child_spans = []
        self.status = status
        self.context_tracer = context_tracer

    @staticmethod
    def on_create(callback):
        pass

    @property
    def children(self):
        """The child spans of the current noopspan."""
        return list()

    def span(self, name='child_span'):
        """Create a child span for the current span and append it to the child
        spans list.

        :type name: str
        :param name: (Optional) The name of the child span.

        :rtype: :class: `~opencensus.trace.noopspan.NoopSpan`
        :returns: A child Span to be added to the current span.
        """
        child_span = NoopSpan(name, parent_span=self)
        self._child_spans.append(child_span)
        return child_span

    def add_attribute(self, attribute_key, attribute_value):
        """No-op implementation of this method.

        :type attribute_key: str
        :param attribute_key: Attribute key.

        :type attribute_value:str
        :param attribute_value: Attribute value.
        """
        pass

    def add_annotation(self, description, **attrs):
        """No-op implementation of this method.

        :type description: str
        :param description: A user-supplied message describing the event.
                        The maximum length for the description is 256 bytes.

        :type attrs: kwargs
        :param attrs: keyworded arguments e.g. failed=True, name='Caching'
        """
        pass

    def add_time_event(self, time_event):
        """No-op implementation of this method.

        :type time_event: :class: `~opencensus.trace.time_event.TimeEvent`
        :param time_event: A TimeEvent object.
        """
        pass

    def add_link(self, link):
        """No-op implementation of this method.

        :type link: :class: `~opencensus.trace.link.Link`
        :param link: A Link object.
        """
        pass

    def start(self):
        """No-op implementation of this method."""
        pass

    def finish(self):
        """No-op implementation of this method."""
        pass

    def __iter__(self):
        """Iterate through the span tree."""
        pass

    def __enter__(self):
        """Start a span."""
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Finish a span."""
        pass

