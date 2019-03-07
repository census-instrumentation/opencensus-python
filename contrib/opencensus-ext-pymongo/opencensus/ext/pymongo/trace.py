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

from pymongo import monitoring

from opencensus.trace import execution_context
from opencensus.trace import span as span_module


log = logging.getLogger(__name__)

MODULE_NAME = 'pymongo'

COMMAND_ATTRIBUTES = ['filter', 'sort', 'skip', 'limit']


def trace_integration(tracer=None):
    """Integrate with pymongo to trace it using event listener."""
    log.info('Integrated module: {}'.format(MODULE_NAME))
    monitoring.register(MongoCommandListener(tracer=tracer))


class MongoCommandListener(monitoring.CommandListener):

    def __init__(self, tracer=None):
        self._tracer = tracer

    @property
    def tracer(self):
        return self._tracer or execution_context.get_opencensus_tracer()

    def started(self, event):
        span = self.tracer.start_span(
            name='{}.{}.{}.{}'.format(MODULE_NAME,
                                      event.database_name,
                                      event.command.get(event.command_name),
                                      event.command_name))
        span.span_kind = span_module.SpanKind.CLIENT

        for attr in COMMAND_ATTRIBUTES:
            _attr = event.command.get(attr, default=None)
            if _attr is not None:
                self.tracer.add_attribute_to_current_span(attr, str(_attr))

        self.tracer.add_attribute_to_current_span(
            'request_id', event.request_id)

        self.tracer.add_attribute_to_current_span(
            'connection_id', str(event.connection_id))

    def succeeded(self, event):
        self._stop('succeeded')

    def failed(self, event):
        self._stop('failed')

    def _stop(self, status):
        self.tracer.add_attribute_to_current_span('status', status)

        self.tracer.end_span()
