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

import mock

from opencensus.ext.mysql import trace


class Test_mysql_trace(unittest.TestCase):

    def test_trace_integration(self):

        def mock_wrap(func):
            return 'mock call'

        mock_call = 'mock call'
        mock_inspect = mock.Mock()
        mock_mysql_module = mock.Mock()

        mock_inspect.getmodule.return_value = mock_mysql_module

        patch_wrap = mock.patch(
            'opencensus.ext.mysql.trace.trace.wrap_conn',
            side_effect=mock_wrap)
        patch_inspect = mock.patch(
            'opencensus.ext.mysql.trace.inspect',
            mock_inspect)

        with patch_wrap, patch_inspect:
            trace.trace_integration()

        self.assertEqual(mock_mysql_module.connect, mock_call)
