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

from django.http import HttpResponse
from django.shortcuts import render

from .forms import HelloForm

from opencensus.trace import config_integration

import mysql.connector
import psycopg2
import sqlalchemy

import os
import requests

DB_HOST = 'localhost'

# MySQL settings
MYSQL_PASSWORD = os.environ.get('SYSTEST_MYSQL_PASSWORD')

# PostgreSQL settings
POSTGRES_PASSWORD = os.environ.get('SYSTEST_POSTGRES_PASSWORD')

INTEGRATIONS = ['mysql', 'postgresql', 'sqlalchemy', 'requests']

config_integration.trace_integrations(INTEGRATIONS)


def home(request):
    return render(request, 'home.html')


def greetings(request):
    if request.method == 'POST':
        form = HelloForm(request.POST)

        if form.is_valid():
            first_name = form.cleaned_data['fname']
            last_name = form.cleaned_data['lname']
            return HttpResponse("Hello, {} {}".format(first_name, last_name))
        else:
            return render(request, 'home.html')

    return render(request, 'home.html')


def trace_requests(request):
    response = requests.get('http://www.google.com')
    return HttpResponse(str(response.status_code))


def mysql_trace(request):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST, user='root', password=MYSQL_PASSWORD)
        cursor = conn.cursor()

        query = 'SELECT 2*3'
        cursor.execute(query)

        result = []

        for item in cursor:
            result.append(item)

        return HttpResponse(str(result))

    except Exception:
        msg = "Query failed. Check your env vars for connection settings."
        return HttpResponse(msg, status=500)


def postgresql_trace(request):
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            user='postgres',
            password=POSTGRES_PASSWORD,
            dbname='postgres')
        cursor = conn.cursor()

        query = 'SELECT 2*3'
        cursor.execute(query)

        result = []

        for item in cursor.fetchall():
            result.append(item)

        return HttpResponse(str(result))

    except Exception:
        msg = "Query failed. Check your env vars for connection settings."
        return HttpResponse(msg, status=500)


def sqlalchemy_mysql_trace(request):
    try:
        engine = sqlalchemy.create_engine(
            'mysql+mysqlconnector://{}:{}@{}'.format('root', MYSQL_PASSWORD,
                                                     DB_HOST))
        conn = engine.connect()

        query = 'SELECT 2*3'

        result_set = conn.execute(query)

        result = []

        for item in result_set:
            result.append(item)

        return HttpResponse(str(result))

    except Exception:
        msg = "Query failed. Check your env vars for connection settings."
        return HttpResponse(msg, status=500)


def sqlalchemy_postgresql_trace(request):
    try:
        engine = sqlalchemy.create_engine('postgresql://{}:{}@{}/{}'.format(
            'postgres', POSTGRES_PASSWORD, DB_HOST, 'postgres'))
        conn = engine.connect()

        query = 'SELECT 2*3'

        result_set = conn.execute(query)

        result = []

        for item in result_set:
            result.append(item)

        return HttpResponse(str(result))

    except Exception:
        msg = "Query failed. Check your env vars for connection settings."
        return HttpResponse(msg, status=500)


def health_check(request):
    return HttpResponse("ok", status=200)


def get_request_header(request):
    return HttpResponse(request.META.get('HTTP_X_CLOUD_TRACE_CONTEXT'))
