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
from opencensus.stats import base_exporter


class TestBaseStats(unittest.TestCase):
    def test_emit(self):
        exp = base_exporter.StatsExporter()
        view_data = []

        with self.assertRaises(NotImplementedError):
            exp.emit(view_data)

    def test_register_view(self):
        exp = base_exporter.StatsExporter()
        view = mock.Mock()

        with self.assertRaises(NotImplementedError):
            exp.on_register_view(view)
