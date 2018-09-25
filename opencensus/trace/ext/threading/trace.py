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

import logging
import threading

from opencensus.trace import execution_context

log = logging.getLogger(__name__)

MODULE_NAME = "threading"


def trace_integration(tracer=None):
    """Wrap the httplib to trace."""
    log.info("Integrated module: {}".format(MODULE_NAME))
    # Wrap the httplib request function
    request_func = getattr(threading.Thread, "start")
    setattr(threading.Thread, request_func.__name__,
            wrap_threading_start(request_func))

    request_func = getattr(threading.Thread, "run")
    setattr(threading.Thread, request_func.__name__,
            wrap_threading_run(request_func))


def wrap_threading_start(request_func):
    """Wrap the start function from thread. Put the tracer informations in the
    threading object.
    """

    def call(self):
        self.__opencensus_tracer = execution_context.get_opencensus_tracer()
        return request_func(self)

    return call


def wrap_threading_run(request_func):
    """Wrap the run function from thread. Get the tracer informations from the
    threading object and set it as current tracer.
    """

    def call(self):
        execution_context.set_opencensus_tracer(self.__opencensus_tracer)
        return request_func(self)

    return call
