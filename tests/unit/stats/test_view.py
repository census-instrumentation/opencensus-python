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
from opencensus.stats import view as view_module


class TestView(unittest.TestCase):

    def test_constructor(self):
        name = "testName"
        description = "testMeasure"
        columns = ["testTagKey1", "testTagKey2"]
        measure = mock.Mock()
        aggregation = mock.Mock()

        view = view_module.View(
            name=name,
            description=description,
            columns=columns,
            measure=measure,
            aggregation=aggregation)

        self.assertEqual("testName", view.name)
        self.assertEqual("testMeasure", view.description)
        self.assertEqual(["testTagKey1", "testTagKey2"], view.columns)
        self.assertEqual(measure, view.measure)
        self.assertEqual(aggregation, view.aggregation)
