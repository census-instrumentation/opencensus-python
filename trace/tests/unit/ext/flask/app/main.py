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

import os
import sys

import flask
import mysql.connector
import psycopg2

from opencensus.trace.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.trace import config_integration
from opencensus.trace.reporters import print_reporter

sys.path.insert(0, os.path.abspath(__file__+"/../../../.."))
from ext import config

INTEGRATIONS = ['mysql', 'postgresql']

app = flask.Flask(__name__)

# Enbale tracing, send traces to Stackdriver Trace
reporter = print_reporter.PrintReporter()
middleware = FlaskMiddleware(app, reporter=reporter)
config_integration.trace_integrations(INTEGRATIONS)


@app.route('/')
def hello():
    return 'hello'


@app.route('/mysql')
def mysql_query():
    try:
        conn = mysql.connector.connect(
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD)
        cursor = conn.cursor()

        query = 'SELECT 2*3'
        cursor.execute(query)

        result = []

        for item in cursor:
            result.append(item)

        return str(result)

    except Exception:
        msg = "Query failed. Check your env vars for connection settings."
        return msg, 500


@app.route('/postgresql')
def postgresql_query():
    try:
        conn = psycopg2.connect(
            host=config.POSTGRES_HOST,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
            dbname=config.POSTGRES_DB)
        cursor = conn.cursor()

        query = 'SELECT * FROM company'
        cursor.execute(query)

        result = []

        for item in cursor.fetchall():
            result.append(item)

        return str(result)

    except Exception:
        msg = "Query failed. Check your env vars for connection settings."
        return msg, 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
