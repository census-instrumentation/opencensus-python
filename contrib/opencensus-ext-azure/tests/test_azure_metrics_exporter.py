# Copyright 2019, OpenCensus Authors
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

import mock
import unittest
from datetime import datetime

from opencensus.ext.azure.common import Options
from opencensus.common import utils
from opencensus.ext.azure import metrics_exporter
from opencensus.metrics import label_key
from opencensus.metrics import label_value
from opencensus.metrics.export import metric
from opencensus.metrics.export import metric_descriptor
from opencensus.metrics.export import value
from opencensus.metrics.export import point
from opencensus.metrics.export import time_series
from opencensus.stats import stats as stats_module


def throw(exc_type, *args, **kwargs):
    def func(*_args, **_kwargs):
        raise exc_type(*args, **kwargs)
    return func

class TestAzureMetricsExporter(unittest.TestCase):
    def test_constructor_missing_key(self):
        instrumentation_key = Options._default.instrumentation_key
        Options._default.instrumentation_key = None
        self.assertRaises(ValueError, lambda: metrics_exporter.MetricsExporter())
        Options._default.instrumentation_key = instrumentation_key

    def test_export_metrics(self):
        lv = label_value.LabelValue('val')
        val = value.ValueLong(value=123)
        dt = datetime(2019, 3, 20, 21, 34, 0, 537954)
        pp = point.Point(value=val, timestamp=dt)

        ts = [
            time_series.TimeSeries(label_values=[lv], points=[pp],
                                   start_timestamp=utils.to_iso_str(dt))
        ]

        desc = metric_descriptor.MetricDescriptor(
            name='name',
            description='description',
            unit='unit',
            type_=metric_descriptor.MetricDescriptorType.GAUGE_INT64,
            label_keys=[label_key.LabelKey('key', 'description')]
        )

        mm = metric.Metric(descriptor=desc, time_series=ts)

        options = Options(instrumentation_key='12345678-1234-5678-abcd-12345678abcd')
        exporter = metrics_exporter.MetricsExporter(options)
        exporter.export_metrics([mm])

        self.assertEqual(exporter.metric_to_envelope.call_count, 1)
        sd_args = exporter.client.create_time_series.call_args[0][1]
        self.assertEqual(len(sd_args), 1)
        [sd_arg] = exporter.client.create_time_series.call_args[0][1]
        self.assertEqual(sd_arg.points[0].value.int64_value, 123)
