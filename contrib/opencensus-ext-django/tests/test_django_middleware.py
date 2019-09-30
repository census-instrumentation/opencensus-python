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
from collections import namedtuple

import django
import mock
import pytest
from django.test.utils import teardown_test_environment

from opencensus.trace import execution_context


class TestOpencensusDatabaseMiddleware(unittest.TestCase):
    def setUp(self):
        from django.conf import settings as django_settings
        from django.test.utils import setup_test_environment

        if not django_settings.configured:
            django_settings.configure()
        setup_test_environment()

    def tearDown(self):
        execution_context.clear()
        teardown_test_environment()

    def test_process_request(self):
        if django.VERSION < (2, 0):
            pytest.skip("Wrong version of Django")

        from opencensus.ext.django import middleware

        sql = "SELECT * FROM users"

        MockConnection = namedtuple('Connection', ('vendor', 'alias'))
        connection = MockConnection('mysql', 'default')

        mock_execute = mock.Mock()
        mock_execute.return_value = "Mock result"

        middleware.OpencensusMiddleware()

        patch_no_tracer = mock.patch(
            'opencensus.ext.django.middleware._get_current_tracer',
            return_value=None)
        with patch_no_tracer:
            result = middleware._trace_db_call(
                mock_execute, sql, params=[], many=False,
                context={'connection': connection})
        self.assertEqual(result, "Mock result")

        mock_tracer = mock.Mock()
        mock_tracer.return_value = mock_tracer
        patch = mock.patch(
            'opencensus.ext.django.middleware._get_current_tracer',
            return_value=mock_tracer)
        with patch:
            result = middleware._trace_db_call(
                mock_execute, sql, params=[], many=False,
                context={'connection': connection})

        (mock_sql, mock_params, mock_many,
            mock_context) = mock_execute.call_args[0]

        self.assertEqual(mock_sql, sql)
        self.assertEqual(mock_params, [])
        self.assertEqual(mock_many, False)
        self.assertEqual(mock_context, {'connection': connection})
        self.assertEqual(result, "Mock result")

        result = middleware._trace_db_call(
            mock_execute, sql, params=[], many=True,
            context={'connection': connection})

        (mock_sql, mock_params, mock_many,
            mock_context) = mock_execute.call_args[0]
        self.assertEqual(mock_many, True)
