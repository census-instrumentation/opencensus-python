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

from opencensus.trace import execution_context
from opencensus.trace import span as span_module

CURSOR_WRAP_METHOD = 'cursor'
QUERY_WRAP_METHODS = ['execute', 'executemany']


def wrap_conn(conn_func):
    """Wrap the mysql conn object with TraceConnection."""
    def call(*args, **kwargs):
        try:
            conn = conn_func(*args, **kwargs)
            cursor_func = getattr(conn, CURSOR_WRAP_METHOD)
            wrapped = wrap_cursor(cursor_func)
            setattr(conn, cursor_func.__name__, wrapped)
            return conn
        except Exception:  # pragma: NO COVER
            logging.warning('Fail to wrap conn, mysql not traced.')
            return conn_func(*args, **kwargs)
    return call


def wrap_cursor(cursor_func):
    def call(*args, **kwargs):
        try:
            cursor = cursor_func(*args, **kwargs)
            for func in QUERY_WRAP_METHODS:
                query_func = getattr(cursor, func)
                wrapped = trace_cursor_query(query_func)
                setattr(cursor, query_func.__name__, wrapped)
            return cursor
        except Exception:  # pragma: NO COVER
            logging.warning('Fail to wrap cursor, mysql not traced.')
            return cursor_func(*args, **kwargs)
    return call


def trace_cursor_query(query_func):
    def call(query, *args, **kwargs):
        _tracer = execution_context.get_opencensus_tracer()
        _span = _tracer.start_span()
        _span.name = 'mysql.query'
        _span.span_kind = span_module.SpanKind.CLIENT
        _tracer.add_attribute_to_current_span('mysql.query', query)
        _tracer.add_attribute_to_current_span(
            'mysql.cursor.method.name',
            query_func.__name__)

        result = query_func(query, *args, **kwargs)

        _tracer.end_span()
        return result
    return call
