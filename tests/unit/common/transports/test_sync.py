# Copyright 2018, OpenCensus Authors
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
from opencensus.common.transports import sync


class TestSyncTransport(unittest.TestCase):
    def test_constructor(self):
        exporter = mock.Mock()
        transport = sync.SyncTransport(exporter)

        self.assertEqual(transport.exporter, exporter)

    def test_export(self):
        exporter = mock.Mock()
        transport = sync.SyncTransport(exporter)
        data = {
            'traceId': 'test1',
            'spans': [{}, {}],
        }
        transport.export(data)
        self.assertTrue(True)
