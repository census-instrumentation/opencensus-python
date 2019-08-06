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

import unittest

from google.rpc import code_pb2
from opencensus.trace import exceptions_status


class TestUtils(unittest.TestCase):
    def test_cancelled(self):
        self.assertEqual(
            exceptions_status.CANCELLED.canonical_code,
            code_pb2.CANCELLED
        )

    def test_invalid_url(self):
        self.assertEqual(
            exceptions_status.INVALID_URL.canonical_code,
            code_pb2.INVALID_ARGUMENT
        )

    def test_timeout(self):
        self.assertEqual(
            exceptions_status.TIMEOUT.canonical_code,
            code_pb2.DEADLINE_EXCEEDED
        )

    def test_unknown(self):
        status = exceptions_status.unknown(Exception)
        self.assertEqual(
            status.canonical_code,
            code_pb2.UNKNOWN
        )
        self.assertEqual(
            status.description,
            str(Exception)
        )
