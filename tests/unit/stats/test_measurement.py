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

from opencensus.stats import measurement as measurement_module

import unittest


class TestMeasurement(unittest.TestCase):
    def test_constructor(self):
        measure = "testMeasure"
        value = 0

        measurement = measurement_module.Measurement(
            measure=measure, value=value)

        self.assertEqual("testMeasure", measurement.measure)
        self.assertEqual(0, measurement.value)


class TestMeasurementInt(unittest.TestCase):
    def test_constructor(self):
        measure = "testIntMeasure"
        value = 10

        measurement = measurement_module.MeasurementInt(
            measure=measure, value=value)

        self.assertEqual("testIntMeasure", measurement.measure)
        self.assertEqual(10, measurement.value)


class TestMeasurementFloat(unittest.TestCase):
    def test_constructor(self):
        measure = "testFloatMeasure"
        value = 10.00

        measurement = measurement_module.MeasurementFloat(
            measure=measure, value=value)

        self.assertEqual("testFloatMeasure", measurement.measure)
        self.assertEqual(10.00, measurement.value)
