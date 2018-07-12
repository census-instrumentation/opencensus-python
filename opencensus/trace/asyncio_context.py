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

import aiotask_context as context

from opencensus.trace.tracers import noop_tracer

_TRACER_KEY = 'opencensus.io/trace'
_ATTRS_KEY = 'opencensus.io/attrs'
_CURRENT_SPAN_KEY = 'opencensus.io/current-span'


def get_opencensus_tracer():
    return context.get(_TRACER_KEY, default=noop_tracer.NoopTracer())


def set_opencensus_tracer(tracer):
    """Add the tracer to thread local."""
    context.set(key=_TRACER_KEY, value=tracer)


def set_opencensus_attr(attr_key, attr_value):
    attrs = context.get(_ATTRS_KEY, {})
    attrs[_ATTRS_KEY] = attr_value
    context.set(key=_ATTRS_KEY, value=attrs)


def get_opencensus_attr(attr_key):
    attrs = context.get(_ATTRS_KEY, None)
    if attrs is not None:
        return attrs.get(_ATTRS_KEY)
    return None


def get_current_span():
    return context.get(_CURRENT_SPAN_KEY, None)


def set_current_span(current_span):
    context.set(key=_CURRENT_SPAN_KEY, value=current_span)


def clear():
    """Clear the thread local, used in test."""
    context.clear()
