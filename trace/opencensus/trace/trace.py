# Copyright 2017 Google Inc.
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

"""This module is for generating Trace object which contains spans."""

import uuid

from opencensus.trace.reporters import file_reporter
from opencensus.trace import trace_span


class Trace(object):
    """A trace describes how long it takes for an application to perform
    an operation. It consists of a set of spans, each of which represent
    a single timed event within the operation. Node that Trace is not
    thread-safe and must not be shared between threads.

    See
    https://cloud.google.com/trace/docs/reference/v1/rpc/google.devtools.
    cloudtrace.v1#google.devtools.cloudtrace.v1.Trace

    :type project_id: str
    :param project_id: (Optional) The project_id for the trace.

    :type trace_id: str
    :param trace_id: (Optional) Trace_id is a 32 hex-digits uuid for the trace.
                     If not given, will generate one automatically.
    """
    def __init__(self, project_id=None, trace_id=None, reporter=None):
        if trace_id is None:
            trace_id = generate_trace_id()

        if reporter is None:
            file_name = '{}_{}'.format(project_id, trace_id)
            reporter = file_reporter.FileReporter(file_name=file_name)

        self.project_id = project_id
        self.trace_id = trace_id
        self.reporter = reporter
        self.spans = []

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.finish()

    def start(self):
        """Start a trace, initialize an empty list of spans."""
        self.spans = []

    def finish(self):
        """Send the trace to Stackdriver Trace API and clear the spans."""
        self.send()
        self.spans = []

    def span(self, name='span'):
        """Create a new span for the trace and append it to the spans list.

        :type name: str
        :param name: (Optional) The name of the span.

        :rtype: :class:`~google.cloud.trace.trace_span.TraceSpan`
        :returns: A TraceSpan to be added to the current Trace.
        """
        span = trace_span.TraceSpan(name)
        self.spans.append(span)
        return span

    def send(self):
        """API call: Patch trace to Stackdriver Trace.

        See
        https://cloud.google.com/trace/docs/reference/v1/rpc/google.devtools.
        cloudtrace.v1#google.devtools.cloudtrace.v1.TraceService.PatchTraces
        """
        spans_list = []
        for root_span in self.spans:
            span_tree = list(iter(root_span))
            span_tree_json = [trace_span.format_span_json(span)
                              for span in span_tree]
            spans_list.extend(span_tree_json)

        if len(spans_list) == 0:
            return

        trace = {
            'projectId': self.project_id,
            'traceId': self.trace_id,
            'spans': spans_list,
        }

        traces = {
            'traces': [trace],
        }

        self.reporter.report(traces)


def generate_trace_id():
    """Generate a trace_id randomly.

    :rtype: str
    :returns: 32 digits randomly generated trace ID.
    """
    trace_id = uuid.uuid4().hex
    return trace_id
