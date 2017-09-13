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
import mysql.connector

from opencensus.trace import execution_context

log = logging.getLogger(__name__)

MODULE_NAME = 'mysql'

CURSOR_WRAP_METHODS = ['execute', 'executemany']
CONN_WRAP_METHODS = ['cursor']


def trace_integration():
    """Wrap the mysql connector to trace it."""
    log.info('Integrated module: {}'.format(MODULE_NAME))
    conn_func = mysql.connector.connect
    conn_module = inspect.getmodule(conn_func)
    wrapped = wrap_conn(conn_func)
    setattr(conn_module, conn_func.__name__, wrapped)


def wrap_conn(conn_func):
    """Wrap the mysql conn object with TraceConnection."""
    def call(*args, **kwargs):
        conn = conn_func(*args, **kwargs)
        cursor_func = conn.cursor
        wrapped = wrap_cursor(cursor_func)
        setattr(conn.__class__, cursor_func.__name__, wrapped)
        print('conn')
        return conn
    return call


def wrap_cursor(cursor_func):
    def call(*args, **kwargs):
        cursor = cursor_func(*args, **kwargs)
        for func in CURSOR_WRAP_METHODS:
            query_func  = getattr(cursor, func)
            wrapped = trace_cursor_query(query_func)
            setattr(cursor.__class__, query_func.__name__, wrapped)
        print('cursor')
        return cursor
    return call


def trace_cursor_query(query_func):
    def call(self, query, *args, **kwargs):
        _tracer = execution_context.get_opencensus_tracer()
        _tracer.start_span()
        _tracer.add_label_to_current_span('mysql.query', query)
        _tracer.add_label_to_current_span(
            'mysql.cursor.method.name',
            query_func.__name__)

        result = query_func(query, *args, **kwargs)

        _tracer.end_span()

        return result
    return call
