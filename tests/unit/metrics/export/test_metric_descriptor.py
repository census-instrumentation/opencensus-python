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

from opencensus.metrics import label_key
from opencensus.metrics.export import metric_descriptor
from opencensus.metrics.export import value

NAME = 'metric'
DESCRIPTION = 'Metric description'
UNIT = '0.738.[ft_i].[lbf_av]/s'
LABEL_KEY1 = label_key.LabelKey('key1', 'key description one')
LABEL_KEY2 = label_key.LabelKey('值', '测试用键')
LABEL_KEYS = (LABEL_KEY1, LABEL_KEY2)


class TestMetricDescriptor(unittest.TestCase):
    def test_init(self):
        md = metric_descriptor.MetricDescriptor(
            NAME, DESCRIPTION, UNIT,
            metric_descriptor.MetricDescriptorType.GAUGE_DOUBLE,
            (LABEL_KEY1, LABEL_KEY2))

        self.assertEqual(md.name, NAME)
        self.assertEqual(md.description, DESCRIPTION)
        self.assertEqual(md.unit, UNIT)
        self.assertEqual(md.type,
                         metric_descriptor.MetricDescriptorType.GAUGE_DOUBLE)
        self.assertEqual(md.label_keys, LABEL_KEYS)

    def test_bogus_type(self):
        with self.assertRaises(ValueError):
            metric_descriptor.MetricDescriptor(NAME, DESCRIPTION, UNIT, 0,
                                               (LABEL_KEY1, ))

    def test_null_label_keys(self):
        with self.assertRaises(ValueError):
            metric_descriptor.MetricDescriptor(
                NAME, DESCRIPTION, UNIT,
                metric_descriptor.MetricDescriptorType.GAUGE_DOUBLE, None)

    def test_empty_label_keys(self):
        metric_descriptor.MetricDescriptor(
            NAME, DESCRIPTION, UNIT,
            metric_descriptor.MetricDescriptorType.GAUGE_DOUBLE, [])

    def test_null_label_key_values(self):
        with self.assertRaises(ValueError):
            metric_descriptor.MetricDescriptor(
                NAME, DESCRIPTION, UNIT,
                metric_descriptor.MetricDescriptorType.GAUGE_DOUBLE, (None, ))

    def test_to_type_class(self):
        self.assertEqual(
            metric_descriptor.MetricDescriptorType.to_type_class(
                metric_descriptor.MetricDescriptorType.GAUGE_INT64),
            value.ValueLong)
        with self.assertRaises(ValueError):
            metric_descriptor.MetricDescriptorType.to_type_class(10)
