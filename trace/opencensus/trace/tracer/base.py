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


class Tracer(object):
    """Base class for Opencensus tracers.

    Subclasses of :class:`Tracer` must implement the below methods.
    """
    def trace(self):
        """Create a trace using the context information.

        :rtype: :class:`~opencensus.trace.trace.Trace`
        :returns: The Trace object.
        """
        raise NotImplementedError

    def start_trace(self):
        """Start a trace."""
        raise NotImplementedError

    def end_trace(self):
        """End a trace."""
        raise NotImplementedError

    def span(self, name='span'):
        """Create a new span with the trace using the context information.

        :type name: str
        :param name: The name of the span.

        :rtype: :class:`~opencensus.trace.trace_span.TraceSpan`
        :returns: The TraceSpan object.
        """
        raise NotImplementedError

    def start_span(self, name='span'):
        """Start a span.

        :type name: str
        :param name: The name of the span.

        :rtype: :class:`~opencensus.trace.trace_span.TraceSpan`
        :returns: The TraceSpan object.
        """
        raise NotImplementedError

    def end_span(self):
        """End a span. Remove the span from the span stack, and update the
        span_id in TraceContext as the current span_id which is the peek
        element in the span stack.
        """
        raise NotImplementedError

    def current_span(self):
        """Return the current span."""
        raise NotImplementedError

    def add_label_to_current_span(self, label_key, label_value):
        raise NotImplementedError

    def add_label_to_spans(self, label_key, label_value):
        """Add label to the spans in current trace.

        :type label_key: str
        :param label_key: Label key.

        :type label_value:str
        :param label_value: Label value.
        """
        raise NotImplementedError

    def list_collected_spans(self):
        """List collected spans."""
        raise NotImplementedError


class NullContextManager(object):
    """Empty object as a helper for faking Trace and TraceSpan when tracing is
    disabled.
    """
    def __init__(self):
        self.name = None

    def __enter__(self):
        pass  # pragma: NO COVER

    def __exit__(self, exc_type, exc_value, traceback):
        pass  # pragma: NO COVER
