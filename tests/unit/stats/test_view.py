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

from opencensus.metrics.export import metric_descriptor
from opencensus.stats import aggregation
from opencensus.stats import measure
from opencensus.stats import view
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

    def test_view_to_metric_descriptor(self):
        mock_measure = mock.Mock(spec=measure.MeasureFloat)
        mock_agg = mock.Mock(spec=aggregation.SumAggregation)
        mock_agg.get_metric_type.return_value = \
            metric_descriptor.MetricDescriptorType.CUMULATIVE_DOUBLE
        test_view = view.View("name", "description", ["tk1", "tk2"],
                              mock_measure, mock_agg)

        self.assertIsNone(test_view._metric_descriptor)
        md = test_view.get_metric_descriptor()
        self.assertTrue(isinstance(md, metric_descriptor.MetricDescriptor))
        self.assertEqual(md.name, test_view.name)
        self.assertEqual(md.description, test_view.description)
        self.assertEqual(md.unit, test_view.measure.unit)
        self.assertEqual(
            md.type, metric_descriptor.MetricDescriptorType.CUMULATIVE_DOUBLE)
        self.assertTrue(
            all(lk.key == col
                for lk, col in zip(md.label_keys, test_view.columns)))

        md_path = ('opencensus.metrics.export.metric_descriptor'
                   '.MetricDescriptor')
        with mock.patch(md_path) as mock_md_cls:
            md2 = test_view.get_metric_descriptor()
            mock_md_cls.assert_not_called()
        self.assertEqual(md, md2)
