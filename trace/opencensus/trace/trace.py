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

"""This module is for generating Trace object which contains spans."""

import uuid

from opencensus.trace import trace_span


class Trace(object):
    """A trace describes how long it takes for an application to perform
    an operation. It consists of a set of spans, each of which represent
    a single timed event within the operation. Node that Trace is not
    thread-safe and must not be shared between threads.

    See
    https://cloud.google.com/trace/docs/reference/v1/rpc/google.devtools.
    cloudtrace.v1#google.devtools.cloudtrace.v1.Trace

    :type trace_id: str
    :param trace_id: (Optional) Trace_id is a 32 hex-digits uuid for the trace.
                     If not given, will generate one automatically.
    """
    def __init__(self, trace_id=None):
        if trace_id is None:
            trace_id = generate_trace_id()

        self.trace_id = trace_id
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
        """Clear the spans."""
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


def generate_trace_id():
    """Generate a trace_id randomly.

    :rtype: str
    :returns: 32 digits randomly generated trace ID.
    """
    trace_id = uuid.uuid4().hex
    return trace_id
