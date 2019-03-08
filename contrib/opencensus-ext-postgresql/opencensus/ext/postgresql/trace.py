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

import inspect
import logging

from opencensus.trace import execution_context
from opencensus.trace import span as span_module

import psycopg2
from psycopg2 import connect as pg_connect
from psycopg2.extensions import cursor as pgcursor

log = logging.getLogger(__name__)

MODULE_NAME = 'postgresql'

CONN_WRAP_METHOD = 'connect'
CURSOR_WRAP_METHOD = 'cursor'
QUERY_WRAP_METHODS = ['execute', 'executemany']


def trace_integration(tracer=None):
    """Wrap the mysql connector to trace it."""
    log.info('Integrated module: {}'.format(MODULE_NAME))
    conn_func = getattr(psycopg2, CONN_WRAP_METHOD)
    conn_module = inspect.getmodule(conn_func)
    setattr(conn_module, conn_func.__name__, connect)


def connect(*args, **kwargs):
    """Create database connection, use TraceCursor as the cursor_factory."""
    kwargs['cursor_factory'] = TraceCursor
    conn = pg_connect(*args, **kwargs)
    return conn


def trace_cursor_query(query_func):
    def call(query, *args, **kwargs):
        _tracer = execution_context.get_opencensus_tracer()
        if _tracer is not None:
            # Note that although get_opencensus_tracer() returns a NoopTracer
            # if no thread local has been set, set_opencensus_tracer() does NOT
            # protect against setting None to the thread local - be defensive
            # here
            _span = _tracer.start_span()
            _span.name = '{}.query'.format(MODULE_NAME)
            _span.span_kind = span_module.SpanKind.CLIENT
            _tracer.add_attribute_to_current_span(
                '{}.query'.format(MODULE_NAME), query)
            _tracer.add_attribute_to_current_span(
                '{}.cursor.method.name'.format(MODULE_NAME),
                query_func.__name__)

        result = query_func(query, *args, **kwargs)

        if _tracer is not None:
            _tracer.end_span()
        return result

    return call


class TraceCursor(pgcursor):

    def __init__(self, *args, **kwargs):  # pragma: NO COVER
        # Tested via rewriting the constructor in unit test, as the parent
        # class is built in and cannot be mocked away.
        for func in QUERY_WRAP_METHODS:
            query_func = getattr(self, func)
            wrapped = trace_cursor_query(query_func)
            setattr(self, query_func.__name__, wrapped)

        super(TraceCursor, self).__init__(*args, **kwargs)
