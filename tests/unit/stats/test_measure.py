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

from opencensus.stats import measure as measure_module


class TestBaseMeasure(unittest.TestCase):
    def test_constructor_defaults(self):
        name = "testName"
        description = "testMeasure"

        measure = measure_module.BaseMeasure(
            name=name, description=description)

        self.assertEqual(None, measure.unit)

    def test_constructor_explicit(self):
        name = "testName"
        description = "testMeasure"
        unit = "testUnit"

        measure = measure_module.BaseMeasure(
            name=name, description=description, unit=unit)

        self.assertEqual("testName", measure.name)
        self.assertEqual("testMeasure", measure.description)
        self.assertEqual("testUnit", measure.unit)


class TestMeasureInt(unittest.TestCase):
    def test_constructor_defaults(self):
        name = "testName"
        description = "testMeasure"

        measure = measure_module.MeasureInt(name=name, description=description)

        self.assertEqual(None, measure.unit)

    def test_constructor_explicit(self):
        name = "testName"
        description = "testMeasure"
        unit = "testUnit"

        measure = measure_module.MeasureInt(
            name=name, description=description, unit=unit)

        self.assertEqual("testName", measure.name)
        self.assertEqual("testMeasure", measure.description)
        self.assertEqual("testUnit", measure.unit)


class TestMeasureFloat(unittest.TestCase):
    def test_constructor_defaults(self):
        name = "testName"
        description = "testMeasure"

        measure = measure_module.MeasureFloat(
            name=name, description=description)

        self.assertEqual(None, measure.unit)

    def test_constructor_explicit(self):
        name = "testName"
        description = "testMeasure"
        unit = "testUnit"

        measure = measure_module.MeasureFloat(
            name=name, description=description, unit=unit)

        self.assertEqual("testName", measure.name)
        self.assertEqual("testMeasure", measure.description)
        self.assertEqual("testUnit", measure.unit)
