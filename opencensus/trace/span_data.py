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

import collections

_SpanData = collections.namedtuple(
    '_SpanData',
    (
        'name',
        'span_id',
        'parent_span_id',
        'attributes',
        'start_time',
        'end_time',
        'stack_trace',
        'time_events',
        'links',
        'status',
        'same_process_as_parent_span',
    ),
)


class SpanData(_SpanData):
    """Immutable representation of all data collected by a
     :class: `~opencensus.trace.span.Span`.

    :type name: str
    :param name: The name of the span.

    :type span_id: int
    :param span_id: Identifier for the span, unique within a trace.

    :type parent_span_id: int
    :param parent_span_id: (Optional) Parent span id.

    :type attributes: dict
    :param attributes: Collection of attributes associated with the span.

    :type start_time: str
    :param start_time: (Optional) Start of the time interval (inclusive)
                       during which the trace data was collected from the
                       application.

    :type end_time: str
    :param end_time: (Optional) End of the time interval (inclusive) during
                     which the trace data was collected from the application.

    :type child_span_count: int
    :param child_span_count: the number of child spans that were
                            generated while the span was active.

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

    """
    __slots__ = ()
