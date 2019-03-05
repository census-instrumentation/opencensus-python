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

from sqlalchemy import engine
from sqlalchemy import event


from opencensus.trace import execution_context
from opencensus.trace import span as span_module

log = logging.getLogger(__name__)

MODULE_NAME = 'sqlalchemy'


def trace_integration(tracer=None):
    """Integrate with SQLAlchemy to trace it using event listener.

    See: http://docs.sqlalchemy.org/en/latest/core/events.html
    """
    log.info('Integrated module: {}'.format(MODULE_NAME))
    trace_engine(engine.Engine)


def trace_engine(engine):
    """Register the event before cursor execute and after cursor execute
    to the event listner of the engine.
    """
    event.listen(engine, 'before_cursor_execute', _before_cursor_execute)
    event.listen(engine, 'after_cursor_execute', _after_cursor_execute)


def _before_cursor_execute(conn, cursor, statement, parameters,
                           context, executemany):
    """Intercept low-level cursor execute() events before execution.
    If executemany is True, this is an executemany call, else an execute call.

    Note: If enabled tracing both SQLAlchemy and the database it connected,
          the communication between SQLAlchemy and the database will also
          be traced. To avoid the verbose spans, you can just trace SQLAlchemy.

    See: http://docs.sqlalchemy.org/en/latest/core/events.html#sqlalchemy.
         events.ConnectionEvents.before_cursor_execute
    """
    # Find out the func name
    if executemany:
        query_func = 'executemany'
    else:
        query_func = 'execute'

    _tracer = execution_context.get_opencensus_tracer()
    _span = _tracer.start_span()
    _span.name = '{}.query'.format(MODULE_NAME)
    _span.span_kind = span_module.SpanKind.CLIENT

    # Set query statement attribute
    _tracer.add_attribute_to_current_span(
        '{}.query'.format(MODULE_NAME), statement)

    # Set query parameters attribute
    _tracer.add_attribute_to_current_span(
        '{}.query.parameters'.format(MODULE_NAME), str(parameters))

    # Set query function attribute
    _tracer.add_attribute_to_current_span(
        '{}.cursor.method.name'.format(MODULE_NAME),
        query_func)


def _after_cursor_execute(conn, cursor, statement, parameters,
                          context, executemany):
    """Intercept low-level cursor execute() events after execution.
    If executemany is True, this is an executemany call, else an execute call.

    See: http://docs.sqlalchemy.org/en/latest/core/events.html#sqlalchemy.
         events.ConnectionEvents.after_cursor_execute
    """
    _tracer = execution_context.get_opencensus_tracer()
    _tracer.end_span()
