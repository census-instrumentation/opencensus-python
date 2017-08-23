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
import unittest


class TestFileReporter(unittest.TestCase):

    @staticmethod
    def _get_target_class():
        from opencensus.trace.reporters.file_reporter import FileReporter

        return FileReporter

    def _make_one(self, *args, **kw):
        return self._get_target_class()(*args, **kw)

    def test_constructor(self):
        file_name = 'file_name'
        reporter = self._make_one(file_name=file_name)

        self.assertEqual(reporter.file_name, file_name)

    def test_report(self):
        import os
        traces = {}
        file_name = 'file_name'
        reporter = self._make_one(file_name=file_name)

        reporter.report(traces)
        assert os.path.exists(file_name) == 1
        os.remove(file_name)
