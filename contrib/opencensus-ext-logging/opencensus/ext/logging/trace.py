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

from opencensus.log import TraceLogger


def trace_integration(tracer=None):
    """Replace the global default logging class with `TraceLogger`.

    Loggers created after the integration will produce `LogRecord`s
    with extra traceId, spanId, and traceSampled attributes from the opencensus
    context.
    """
    logging.setLoggerClass(TraceLogger)
