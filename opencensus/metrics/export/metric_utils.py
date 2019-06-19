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
"""
Utilities to convert raw measures to metrics
"""

from opencensus.metrics.export import point
from opencensus.metrics.export import time_series
from opencensus.metrics.export import value
from opencensus.metrics.export import metric_descriptor
from opencensus.metrics.export.measure import MeasureType
from opencensus.metrics.export import metric

def measure_to_metric(measure):
    measurement = measure.measurement
    p = None
    md_type = None

    if measure.measure_type == MeasureType.DOUBLE:
        md_type = metric_descriptor.MetricDescriptorType.GAUGE_DOUBLE
        p = point.Point(value.ValueDouble(measurement.value), measurement.timestamp)
    else:
        md_type = metric_descriptor.MetricDescriptorType.GAUGE_INT64
        p = point.Point(value.ValueLong(measurement.value), measurement.timestamp)
        
    md = metric_descriptor.MetricDescriptor(measure.name, measure.description, measure.unit, md_type, {})
    ts = [time_series.TimeSeries({}, [p], None)]

    return metric.Metric(md, ts)