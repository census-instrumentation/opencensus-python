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


class TestFileExporter(unittest.TestCase):

    @staticmethod
    def _get_target_class():
        from opencensus.trace.exporters.print_exporter import PrintExporter

        return PrintExporter

    def _make_one(self, *args, **kw):
        return self._get_target_class()(*args, **kw)

    def test_export(self):
        traces = {}
        exporter = self._make_one()

        printed = exporter.export(traces)
        self.assertEqual(printed, traces)
