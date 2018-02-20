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

from opencensus.trace import status as status_module


class TestStatus(unittest.TestCase):
    def test_constructor(self):
        code = 100
        message = 'test message'
        status = status_module.Status(code=code, message=message)

        self.assertEqual(status.code, code)
        self.assertEqual(status.message, message)
        self.assertIsNone(status.details)

    def test_format_status_json_with_details(self):
        code = 100
        message = 'test message'
        details = [
            {
                '@type': 'string',
                'field1': 'value',
            },
        ]
        status = status_module.Status(
            code=code, message=message, details=details)
        status_json = status.format_status_json()

        expected_status_json = {
            'code': code,
            'message': message,
            'details': details
        }

        self.assertEqual(expected_status_json, status_json)

    def test_format_status_json_without_details(self):
        code = 100
        message = 'test message'

        status = status_module.Status(code=code, message=message)
        status_json = status.format_status_json()

        expected_status_json = {
            'code': code,
            'message': message
        }

        self.assertEqual(expected_status_json, status_json)

    def test_create_from_exception(self):
        message = 'test message'
        exc = ValueError(message)
        status = status_module.Status.from_exception(exc)
        self.assertEqual(status.message, message)
        self.assertEqual(status.code, code_pb2.UNKNOWN)
