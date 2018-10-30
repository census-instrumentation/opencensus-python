# -*- coding: utf-8 -*-

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

from opencensus.metrics.export.metric_descriptor import MetricDescriptor
from opencensus.metrics.export.metric_descriptor import MetricDescriptorType
from opencensus.metrics.label_key import LabelKey

NAME = 'metric'
DESCRIPTION = 'Metric description'
UNIT = '0.738.[ft_i].[lbf_av]/s'
LABEL_KEY1 = LabelKey('key1', 'key description one')
LABEL_KEY2 = LabelKey('值', '测试用键')
LABEL_KEYS = (LABEL_KEY1, LABEL_KEY2)


class TestMetricDescriptor(unittest.TestCase):
    def test_init(self):
        metric_descriptor = MetricDescriptor(NAME, DESCRIPTION, UNIT,
                                             MetricDescriptorType.GAUGE_DOUBLE,
                                             (LABEL_KEY1, LABEL_KEY2))

        self.assertEqual(metric_descriptor.name, NAME)
        self.assertEqual(metric_descriptor.description, DESCRIPTION)
        self.assertEqual(metric_descriptor.unit, UNIT)
        self.assertEqual(metric_descriptor.type,
                         MetricDescriptorType.GAUGE_DOUBLE)
        self.assertEqual(metric_descriptor.label_keys, LABEL_KEYS)

    def test_bogus_type(self):
        with self.assertRaises(ValueError):
            MetricDescriptor(NAME, DESCRIPTION, UNIT, 0, (LABEL_KEY1, ))

    def test_null_label_keys(self):
        with self.assertRaises(ValueError):
            MetricDescriptor(NAME, DESCRIPTION, UNIT,
                             MetricDescriptorType.GAUGE_DOUBLE, None)

    def test_null_label_key_values(self):
        with self.assertRaises(ValueError):
            MetricDescriptor(NAME, DESCRIPTION, UNIT,
                             MetricDescriptorType.GAUGE_DOUBLE, (None, ))

    def test_to_type_class(self):
        self.assertEqual(
            MetricDescriptorType.to_type_class(
                MetricDescriptorType.GAUGE_INT64), int)
        with self.assertRaises(ValueError):
            MetricDescriptorType.to_type_class(10)
