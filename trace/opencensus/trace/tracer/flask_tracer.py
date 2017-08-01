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

"""The FlaskTracer maintains the trace spans for a trace in flask application.
It has a stack of TraceSpan that are currently open allowing you to know the
current context at any moment.
"""

try:
    import flask
except ImportError:  # pragma: NO COVER
    flask = None

from opencensus.trace.propagation.google_cloud_format import from_header
from opencensus.trace.tracer.context_tracer import ContextTracer

_FLASK_TRACE_KEY = 'X_CLOUD_TRACE_CONTEXT'


class FlaskTracer(ContextTracer):
    """The flask implementation of the ContextTracer Interface.

    :type span_context: :class:`~opencensus.trace.span_context.SpanContext`
    :param span_context: The current span context.

    :type sampler: :class:`type`
    :param sampler: Class for creating new Sampler objects. It should extend
                    from the base :class:`.Sampler` type and implement
                    :meth:`.Sampler.should_sample`. Defaults to
                    :class:`.AlwaysOnSampler`. The rest options are
                    :class:`.AlwaysOffSampler`, :class:`.FixedRateSampler`.

    :type reporter: :class:`type`
    :param reporter: Class for creating new Reporter objects. Default to
                     :class:`.PrintReporter`. The rest option is
                     :class:`.FileReporter`.
    """
    def __init__(self, span_context=None, sampler=None, reporter=None):
        if span_context is None:
            header = get_flask_header()
            span_context = from_header(header)

        super(FlaskTracer, self).__init__(
            span_context=span_context,
            sampler=sampler,
            reporter=reporter)


def get_flask_header():
    """Get trace context header from flask request headers.

    :rtype: str
    :returns: Trace context header in HTTP request headers.
    """
    if flask is None or not flask.request:
        return None

    header = flask.request.headers.get(_FLASK_TRACE_KEY)

    return header
