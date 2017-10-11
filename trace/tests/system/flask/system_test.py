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

import multiprocessing as mp
import os
import random
import requests
import signal
import subprocess
import time
import uuid

import unittest

PROJECT = os.environ.get('GCLOUD_PROJECT_PYTHON')


def wait_app_to_start(headers):
    retry = 0
    while True:
        try:
            retry += 1
            if retry > 10:
                break

            response = requests.get('http://127.0.0.1:8080', headers=headers)
            break
        except Exception:
            time.sleep(1)


def generate_header():
    """Generate a trace header."""
    trace_id = uuid.uuid4().hex
    span_id = random.getrandbits(64)
    trace_option = 1

    header = '{}/{};o={}'.format(trace_id, span_id, trace_option)

    return trace_id, span_id, header


def run_application():
    cmd = 'python tests/system/flask/main.py'
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        shell=True,
        preexec_fn=os.setsid)
    return process


class TestFlaskTrace(unittest.TestCase):

    def setUp(self):
        from google.cloud import trace

        # Generate trace headers
        trace_id, span_id, trace_header = generate_header()
        self.trace_id = trace_id
        self.span_id = span_id
        self.trace_header = trace_header

        # Run application
        self.process = run_application()

        # Wait the application to start
        headers = {
            'X_CLOUD_TRACE_CONTEXT': self.trace_header
        }
        wait_app_to_start(headers)

        # Initialize the stackdriver trace client
        self.client = trace.Client(project=PROJECT)

    def tearDown(self):
        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

    def test_flask_request_trace(self):
        subprocess.call(
            ['curl', '-v', '--header',
             self.trace_header, 'http://127.0.0.1:8080'])

        trace = self.client.get_trace(trace_id=self.trace_id)

        self.assertEqual(trace.get('projectId'), PROJECT)
        self.assertEqual(trace.get('traceId'), str(self.trace_id))
        self.assertNotEqual(len(trace.get('spans')), 0)
        self.assertEqual(
            trace.get('spans')[0].get('parentSpanId'),
            str(self.span_id))


# For running test in when debugging locally
if __name__ == '__main__':
    test = TestFlaskTrace()
    test.setUp()
    test.test_connection()
    test.tearDown()
