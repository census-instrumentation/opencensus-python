# Copyright 2018, OpenCensus Authors
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

import logging
import threading
from multiprocessing import pool

from opencensus.trace import execution_context

log = logging.getLogger(__name__)

MODULE_NAME = "threading"


def trace_integration(tracer=None):
    """Wrap threading functions to trace."""
    log.info("Integrated module: {}".format(MODULE_NAME))
    # Wrap the threading start function
    start_func = getattr(threading.Thread, "start")
    setattr(threading.Thread, start_func.__name__,
            wrap_threading_start(start_func))

    # Wrap the threading run function
    run_func = getattr(threading.Thread, "run")
    setattr(threading.Thread, run_func.__name__,
            wrap_threading_run(run_func))

    # Wrap the threading run function
    queue_func = getattr(pool.ThreadPool, "apply_async")
    setattr(pool.Pool, queue_func.__name__,
            wrap_apply_async(queue_func))


def wrap_threading_start(start_func):
    """Wrap the start function from thread. Put the tracer informations in the
    threading object.
    """

    def call(self):
        self._opencensus_context = execution_context.get_opencensus_full_context()
        return start_func(self)

    return call


def wrap_threading_run(run_func):
    """Wrap the run function from thread. Get the tracer informations from the
    threading object and set it as current tracer.
    """

    def call(self):
        execution_context.set_opencensus_full_context(*self._opencensus_context)
        return run_func(self)

    return call


def wrap_apply_async(apply_async_func):
    """Wrap the apply_async function of multiprocessing.pools. Get the function
    that will be called and wrap it then add the opencensus context."""

    def call(self, func, args=(), kwds={}, **kwargs):
        func = wrap_task_func(func)
        kwds['_opencensus_context'] = execution_context.get_opencensus_full_context()
        return apply_async_func(self, func, args=args, kwds=kwds, **kwargs)

    return call


def wrap_task_func(task_func):
    """Wrap the function given to apply_async to get the tracer from context,
    execute the function then clear the context."""

    def call(*args, **kwargs):
        _opencensus_context = kwargs.pop('_opencensus_context')
        execution_context.set_opencensus_full_context(*_opencensus_context)
        result = task_func(*args, **kwargs)
        execution_context.clean()
        return result

    return call
