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

from opencensus.trace.ext.dbapi import trace

MODULE_NAME = 'mysql'

CONN_WRAP_METHOD = 'connect'


def trace_integration():
    """Wrap the mysql connector to trace it."""
    logging.info('Integrated module: {}'.format(MODULE_NAME))
    conn_func = getattr(mysql.connector, CONN_WRAP_METHOD)
    conn_module = inspect.getmodule(conn_func)
    wrapped = trace.wrap_conn(conn_func)
    setattr(conn_module, CONN_WRAP_METHOD, wrapped)
