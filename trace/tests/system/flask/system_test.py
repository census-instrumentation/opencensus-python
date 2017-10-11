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
import random
import requests
import subprocess
import time
import uuid

import unittest

PROJECT = os.environ.get('GCLOUD_PROJECT')


def set_credential():
    subprocess.call(['./set_credential.sh'], shell=True)


def wait_app_to_start():
    while True:
        try:
            response = requests.get('http://127.0.0.1:8080')
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


class WorkerProcess(mp.Process):

    def __init__(self):
        mp.Process.__init__(self)
        self.exit = mp.Event()

    def run(self):
        subprocess.call(['python', 'main.py'])

    def shutdown(self):
        process = mp.active_children()
        for p in process:
            p.terminate()
            print('killed')


class TestFlaskTrace(unittest.TestCase):

    def setUp(self):
        from google.cloud import trace

        trace_id, span_id, trace_header = generate_header()
        self.trace_id = trace_id
        self.span_id = span_id
        self.trace_header = trace_header

        set_credential()
        self.worker = WorkerProcess()
        self.worker.start()
        wait_app_to_start()

        self.client = trace.Client(project=PROJECT)

    def tearDown(self):
        self.worker.shutdown()

    def test_connection(self):
        subprocess.call(
            ['curl', '-v', '--header',
             self.trace_header, 'http://127.0.0.1:8080'])

        # trace = self.client.get_trace(trace_id=self.trace_id)
        #
        # self.assertEqual(trace, {})


if __name__ == '__main__':
    test = TestFlaskTrace()
    test.setUp()
    test.test_connection()
    test.tearDown()
