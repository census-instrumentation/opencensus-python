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

import wrapt

from opencensus.trace import thread_local

log = logging.getLogger(__name__)

MODULE_NAME = 'mysql'


def trace():
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
        wrapped = TraceConnection(conn)
        return wrapped
    return call


class TraceConnection(wrapt.ObjectProxy):
    """Trace MySQL connection."""

    def __init__(self, conn):
        super(TraceConnection, self).__init__(conn)
        self.conn = conn

    def cursor(self, *args, **kwargs):
        cursor = self.conn.cursor(*args, **kwargs)
        return TraceCursor(cursor)


class TraceCursor(wrapt.ObjectProxy):
    """Trace MySQL cursor methods."""

    def __init__(self, cursor):
        super(TraceCursor, self).__init__(cursor)
        self.cursor = cursor
        self.tracer = thread_local.get_opencensus_tracer()

    def trace_cursor_query(self, method, query, *args, **kwargs):
        self.tracer.start_span()
        self.tracer.add_label_to_current_span('mysql.query', query)
        self.tracer.add_label_to_current_span(
            'cursor.method.name',
            method.__name__)

        result = method(*args, **kwargs)

        self.tracer.end_span()

        return result

    def execute(self, query, *args, **kwargs):
        """
        Note: execute() command already waits for the command to be completely
        executed before passing to the next line of code.
        """
        return self.trace_cursor_query(
            self.cursor.execute,
            query,
            query,
            *args,
            **kwargs)

    def executemany(self, query, *args, **kwargs):
        """
        Note: executemany() command already waits for the command to be
        completely executed before passing to the next line of code.
        """
        return self.trace_cursor_query(
            self.cursor.executemany,
            query,
            query,
            *args,
            **kwargs)
