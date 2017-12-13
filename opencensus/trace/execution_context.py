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

import threading

from opencensus.trace.tracers import noop_tracer

_thread_local = threading.local()


def get_opencensus_tracer():
    """Get the opencensus tracer from thread local."""
    return getattr(_thread_local, 'tracer', noop_tracer.NoopTracer())


def set_opencensus_tracer(tracer):
    """Add the tracer to thread local."""
    setattr(_thread_local, 'tracer', tracer)


def set_opencensus_attr(attr_key, attr_value):
    # If there is no attrs, initialize it to empty dict.
    attrs = getattr(_thread_local, 'attrs', {})

    attrs[attr_key] = attr_value

    setattr(_thread_local, 'attrs', attrs)


def get_opencensus_attr(attr_key):
    attrs = getattr(_thread_local, 'attrs', None)

    if attrs is not None:
        return attrs.get(attr_key)

    return None


def get_current_span():
    return getattr(_thread_local, 'current_span', None)


def set_current_span(current_span):
    setattr(_thread_local, 'current_span', current_span)


def clear():
    """Clear the thread local, used in test."""
    _thread_local.__dict__.clear()
