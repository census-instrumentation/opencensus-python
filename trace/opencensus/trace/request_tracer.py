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

from opencensus.trace.propagation import google_cloud_format
from opencensus.trace.reporters import print_reporter
from opencensus.trace.samplers import always_on
from opencensus.trace.span_context import SpanContext
from opencensus.trace.tracer import context_tracer
from opencensus.trace.tracer import noop_tracer
from opencensus.trace import execution_context


class RequestTracer(object):
    """The RequestTracer is for tracing a request for web applications.

    :type span_context: :class:`~opencensus.trace.span_context.SpanContext`
    :param span_context: SpanContext encapsulates the current context within
                         the request's trace.

    :type sampler: :class:`~opencensus.trace.samplers.base.Sampler`
    :param sampler: Instances of Sampler objects. Defaults to
                    :class:`.AlwaysOnSampler`. The rest options are
                    :class:`.AlwaysOffSampler`, :class:`.FixedRateSampler`.

    :type reporter: :class:`~opencensus.trace.reporters.base.Reporter`
    :param reporter: Instances of Reporter objects. Default to
                     :class:`.PrintReporter`. The rest options are
                     :class:`.FileReporter`, :class:`.PrintReporter`,
                     :class:`.LoggingReporter`, :class:`.ZipkinReporter`,
                     :class:`.GoogleCloudReporter`
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
            sampler = always_on.AlwaysOnSampler()

        if reporter is None:
            reporter = print_reporter.PrintReporter()

        if propagator is None:
            propagator = google_cloud_format.GoogleCloudFormatPropagator()

        self.span_context = span_context
        self.sampler = sampler
        self.reporter = reporter
        self.propagator = propagator
        self.tracer = self.get_tracer()
        self.store_tracer()

    def should_sample(self):
        """Determine whether to sample this request or not.
        If the context forces not tracing, just set enabled to False.
        Else follow the sampler.

        :rtype: bool
        :returns: Whether to trace the request or not.
        """
        return self.span_context.enabled and self.sampler.should_sample

    def get_tracer(self):
        """Return a tracer according to the sampling decision."""
        sampled = self.should_sample()

        if sampled:
            return context_tracer.ContextTracer(self.span_context)
        else:
            return noop_tracer.NoopTracer()

    def store_tracer(self):
        """Add the current tracer to thread_local"""
        execution_context.set_opencensus_tracer(self)

    def start_trace(self):
        """Start a trace."""
        self.tracer.start_trace()

    def end_trace(self):
        """End a trace and send trace using reporter."""
        trace = self.tracer.end_trace()

        if trace is not None:
            self.reporter.report(trace)

    def span(self, name=None):
        """Create a new span with the trace using the context information.

        :type name: str
        :param name: The name of the span.

        :rtype: :class:`~opencensus.trace.trace_span.TraceSpan`
        :returns: The TraceSpan object.
        """
        return self.tracer.span(name)

    def start_span(self, name=None):
        return self.tracer.start_span(name)

    def end_span(self):
        """End a span. Remove the span from the span stack, and update the
        span_id in TraceContext as the current span_id which is the peek
        element in the span stack.
        """
        self.tracer.end_span()

    def current_span(self):
        """Return the current span."""
        return self.tracer.current_span()

    def add_label_to_current_span(self, label_key, label_value):
        """Add label to current span.

        :type label_key: str
        :param label_key: Label key.

        :type label_value:str
        :param label_value: Label value.
        """
        self.tracer.add_label_to_current_span(label_key, label_value)

    def add_label_to_spans(self, label_key, label_value):
        self.tracer.add_label_to_spans(label_key, label_value)

    def trace_decorator(self):
        """Decorator to trace a function."""

        def decorator(func):

            def wrapper(*args, **kwargs):
                self.tracer.start_span(name=func.__name__)
                return_value = func(*args, **kwargs)
                self.tracer.end_span()
                return return_value

            return wrapper

        return decorator
