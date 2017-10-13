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
import random
import requests
import shlex
import signal
import subprocess
import time
import uuid

import unittest

PROJECT = os.environ.get('GCLOUD_PROJECT_PYTHON')


def wait_app_to_start():
    """Wait the application to start running."""
    cmd = 'until nc -z -v -w30 127.0.0.1 8000; do sleep 2; done'
    os.system(cmd)


def generate_header():
    """Generate a trace header."""
    trace_id = uuid.uuid4().hex
    span_id = random.getrandbits(64)
    trace_option = 1

    header = '{}/{};o={}'.format(trace_id, span_id, trace_option)

    return trace_id, span_id, header


def run_application():
    """Start running the django application."""
    cmd = 'python tests/system/django/manage.py runserver'
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        shell=True,
        preexec_fn=os.setsid)
    return process


class TestdjangoTrace(unittest.TestCase):

    def setUp(self):
        from google.cloud import trace

        # Generate trace headers
        trace_id, span_id, trace_header = generate_header()
        self.trace_id = trace_id
        self.span_id = span_id
        self.trace_header = trace_header

        print(self.trace_header)

        # Run application
        self.process = run_application()

        self.headers_trace = {
            'x-cloud-trace-context': '{}/{};o={}'.format(
                self.trace_id, self.span_id, 1)
        }

        # Wait the application to start
        wait_app_to_start()

        # Initialize the stackdriver trace client
        self.client = trace.Client(project=PROJECT)

        self.container_to_delete = []

    def tearDown(self):
        # Kill the django application process
        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

        # Stop and remove the running containers
        for container_id in self.container_to_delete:
            # Stop container
            subprocess.call(
                shlex.split('docker stop {}'.format(container_id)))

            # Remove container
            subprocess.call(
                shlex.split('docker rm {}'.format(container_id)))

    def test_django_request_trace(self):
        requests.get(
            'http://127.0.0.1:8000',
            headers=self.headers_trace)

        time.sleep(5)

        trace = self.client.get_trace(trace_id=self.trace_id)

        self.assertEqual(trace.get('projectId'), PROJECT)
        self.assertEqual(trace.get('traceId'), str(self.trace_id))
        self.assertEqual(len(trace.get('spans')), 1)
        self.assertEqual(
            trace.get('spans')[0].get('parentSpanId'),
            str(self.span_id))

    def test_mysql_trace(self):
        subprocess.call(
            ['./tests/system/containers/mysql/setup.sh'], shell=True)

        requests.get(
            'http://127.0.0.1:8000/mysql',
            headers=self.headers_trace)

        time.sleep(5)

        trace = self.client.get_trace(trace_id=self.trace_id)

        self.assertEqual(trace.get('projectId'), PROJECT)
        self.assertEqual(trace.get('traceId'), str(self.trace_id))

        # Should have 2 spans, one for django request, one for mysql query
        self.assertEqual(len(trace.get('spans')), 2)
        self.assertEqual(
            trace.get('spans')[0].get('parentSpanId'),
            str(self.span_id))

        # Get mysql contianer id, convert it from byte to string
        mysql_container_id = subprocess.check_output(
            shlex.split('docker ps -aqf name=systest_mysql')) \
            .decode('utf-8') \
            .strip()

        self.container_to_delete.append(mysql_container_id)

    def test_postgresql_trace(self):
        subprocess.call(
            ['./tests/system/containers/postgresql/setup.sh'], shell=True)

        requests.get(
            'http://127.0.0.1:8000/postgresql',
            headers=self.headers_trace)

        time.sleep(5)

        trace = self.client.get_trace(trace_id=self.trace_id)

        self.assertEqual(trace.get('projectId'), PROJECT)
        self.assertEqual(trace.get('traceId'), str(self.trace_id))

        # Should have 2 spans, one for django request, one for postgresql query
        self.assertEqual(len(trace.get('spans')), 2)
        self.assertEqual(
            trace.get('spans')[0].get('parentSpanId'),
            str(self.span_id))

        # Get postgresql contianer id, convert it from byte to string
        postgresql_container_id = subprocess.check_output(
            shlex.split('docker ps -aqf name=systest_postgresql')) \
            .decode('utf-8') \
            .strip()

        self.container_to_delete.append(postgresql_container_id)

    def test_sqlalchemy_mysql_trace(self):
        subprocess.call(
            ['./tests/system/containers/mysql/setup.sh'], shell=True)

        requests.get(
            'http://127.0.0.1:8000/sqlalchemy_mysql',
            headers=self.headers_trace)

        time.sleep(5)

        trace = self.client.get_trace(trace_id=self.trace_id)

        self.assertEqual(trace.get('projectId'), PROJECT)
        self.assertEqual(trace.get('traceId'), str(self.trace_id))
        self.assertNotEqual(len(trace.get('spans')), 0)
        self.assertEqual(
            trace.get('spans')[0].get('parentSpanId'),
            str(self.span_id))

        # Get mysql contianer id, convert it from byte to string
        mysql_container_id = subprocess.check_output(
            shlex.split('docker ps -aqf name=systest_mysql')) \
            .decode('utf-8') \
            .strip()

        self.container_to_delete.append(mysql_container_id)

    def test_sqlalchemy_postgresql_trace(self):
        subprocess.call(
            ['./tests/system/containers/postgresql/setup.sh'], shell=True)

        requests.get(
            'http://127.0.0.1:8000/sqlalchemy_postgresql',
            headers=self.headers_trace)

        time.sleep(5)

        trace = self.client.get_trace(trace_id=self.trace_id)

        self.assertEqual(trace.get('projectId'), PROJECT)
        self.assertEqual(trace.get('traceId'), str(self.trace_id))
        self.assertNotEqual(len(trace.get('spans')), 0)
        self.assertEqual(
            trace.get('spans')[0].get('parentSpanId'),
            str(self.span_id))

        # Get postgresql contianer id, convert it from byte to string
        postgresql_container_id = subprocess.check_output(
            shlex.split('docker ps -aqf name=systest_postgresql')) \
            .decode('utf-8') \
            .strip()

        self.container_to_delete.append(postgresql_container_id)
