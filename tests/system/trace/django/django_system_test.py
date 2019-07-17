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
import requests
import signal
import subprocess
import uuid

from retrying import retry

import unittest

PROJECT = os.environ.get('GCLOUD_PROJECT_PYTHON')

HOST_PORT = 'localhost:8000'
BASE_URL = 'http://localhost:8000/'

RETRY_WAIT_PERIOD = 8000  # Wait 8 seconds between each retry
RETRY_MAX_ATTEMPT = 10  # Retry 10 times


def wait_app_to_start():
    """Wait the application to start running."""
    cmd = 'wget --retry-connrefused --tries=5 {}'.format(BASE_URL)
    subprocess.check_call(cmd, shell=True)


def generate_header():
    """Generate a trace header."""
    trace_id = uuid.uuid4().hex
    span_id = uuid.uuid4().hex[:16]
    trace_option = 1

    header = '{}/{};o={}'.format(trace_id, int(span_id, 16), trace_option)

    return trace_id, span_id, header


def run_application():
    """Start running the django application."""
    cmd = 'python tests/system/trace/django/manage.py runserver {}'.format(
        HOST_PORT)
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
    return process


class TestDjangoTrace(unittest.TestCase):
    def setUp(self):
        from google.cloud.trace.v1 import client as client_module

        # Generate trace headers
        trace_id, span_id, trace_header = generate_header()
        self.trace_id = trace_id
        self.span_id = span_id
        self.trace_header = trace_header

        print(self.trace_header)

        # Run application
        self.process = run_application()

        self.headers_trace = {
            'x-cloud-trace-context':
            '{}/{};o={}'.format(self.trace_id, int(self.span_id, 16), 1)
        }

        # Wait the application to start
        wait_app_to_start()

        # Initialize the stackdriver trace client
        self.client = client_module.Client(project=PROJECT)

    def tearDown(self):
        # Kill the django application process
        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

    def test_django_request_trace(self):
        requests.get(BASE_URL, headers=self.headers_trace)

        @retry(
            wait_fixed=RETRY_WAIT_PERIOD,
            stop_max_attempt_number=RETRY_MAX_ATTEMPT)
        def test_with_retry(self):
            trace = self.client.get_trace(trace_id=self.trace_id)
            spans = trace.get('spans')

            self.assertEqual(trace.get('projectId'), PROJECT)
            self.assertEqual(trace.get('traceId'), str(self.trace_id))
            self.assertEqual(len(spans), 1)

            for span in spans:
                labels = span.get('labels')
                self.assertEqual(labels.get('/http/status_code'), '200')

        test_with_retry(self)

    def test_mysql_trace(self):
        requests.get('{}mysql'.format(BASE_URL), headers=self.headers_trace)

        @retry(
            wait_fixed=RETRY_WAIT_PERIOD,
            stop_max_attempt_number=RETRY_MAX_ATTEMPT)
        def test_with_retry(self):
            trace = self.client.get_trace(trace_id=self.trace_id)
            spans = trace.get('spans')

            self.assertEqual(trace.get('projectId'), PROJECT)
            self.assertEqual(trace.get('traceId'), str(self.trace_id))

            # Should have 2 spans, one for django request, one for mysql query
            self.assertEqual(len(spans), 2)

            request_succeeded = False

            for span in spans:
                labels = span.get('labels')
                if '/http/status_code' in labels.keys():
                    self.assertEqual(labels.get('/http/status_code'), '200')
                    request_succeeded = True

                if span.get('name') == '[mysql.query]SELECT 2*3':
                    self.assertEqual(
                        labels.get('mysql.cursor.method.name'), 'execute')
                    self.assertEqual(labels.get('mysql.query'), 'SELECT 2*3')

            self.assertTrue(request_succeeded)

        test_with_retry(self)

    def test_postgresql_trace(self):
        requests.get(
            '{}postgresql'.format(BASE_URL), headers=self.headers_trace)

        @retry(
            wait_fixed=RETRY_WAIT_PERIOD,
            stop_max_attempt_number=RETRY_MAX_ATTEMPT)
        def test_with_retry(self):
            trace = self.client.get_trace(trace_id=self.trace_id)
            spans = trace.get('spans')

            self.assertEqual(trace.get('projectId'), PROJECT)
            self.assertEqual(trace.get('traceId'), str(self.trace_id))

            # Should have 2 spans, one for django request, one for postgresql
            # query
            self.assertEqual(len(trace.get('spans')), 2)

            request_succeeded = False

            for span in spans:
                labels = span.get('labels')
                if '/http/status_code' in labels.keys():
                    self.assertEqual(labels.get('/http/status_code'), '200')
                    request_succeeded = True

                if span.get('name') == '[postgresql.query]SELECT 2*3':
                    self.assertEqual(
                        labels.get('postgresql.cursor.method.name'), 'execute')
                    self.assertEqual(
                        labels.get('postgresql.query'), 'SELECT 2*3')

            self.assertTrue(request_succeeded)

        test_with_retry(self)

    def test_sqlalchemy_mysql_trace(self):
        requests.get(
            '{}sqlalchemy_mysql'.format(BASE_URL), headers=self.headers_trace)

        @retry(
            wait_fixed=RETRY_WAIT_PERIOD,
            stop_max_attempt_number=RETRY_MAX_ATTEMPT)
        def test_with_retry(self):
            trace = self.client.get_trace(trace_id=self.trace_id)
            spans = trace.get('spans')

            self.assertEqual(trace.get('projectId'), PROJECT)
            self.assertEqual(trace.get('traceId'), str(self.trace_id))
            self.assertNotEqual(len(trace.get('spans')), 0)

            request_succeeded = False

            for span in spans:
                labels = span.get('labels')
                if '/http/status_code' in labels.keys():
                    self.assertEqual(labels.get('/http/status_code'), '200')
                    request_succeeded = True

            self.assertTrue(request_succeeded)

        test_with_retry(self)

    def test_sqlalchemy_postgresql_trace(self):
        requests.get(
            '{}sqlalchemy_postgresql'.format(BASE_URL),
            headers=self.headers_trace)

        @retry(
            wait_fixed=RETRY_WAIT_PERIOD,
            stop_max_attempt_number=RETRY_MAX_ATTEMPT)
        def test_with_retry(self):
            trace = self.client.get_trace(trace_id=self.trace_id)
            spans = trace.get('spans')

            self.assertEqual(trace.get('projectId'), PROJECT)
            self.assertEqual(trace.get('traceId'), str(self.trace_id))
            self.assertNotEqual(len(trace.get('spans')), 0)

            request_succeeded = False

            for span in spans:
                labels = span.get('labels')
                if '/http/status_code' in labels.keys():
                    self.assertEqual(labels.get('/http/status_code'), '200')
                    request_succeeded = True

            self.assertTrue(request_succeeded)

        test_with_retry(self)
