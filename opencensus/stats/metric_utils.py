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
"""
Utilities to convert stats data models to metrics data models.
"""

from opencensus.metrics import label_value
from opencensus.metrics.export import metric
from opencensus.metrics.export import metric_descriptor
from opencensus.metrics.export import time_series
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module

# To check that an aggregation's reported type matches its class
AGGREGATION_TYPE_MAP = {
    aggregation_module.Type.SUM:
    aggregation_module.SumAggregation,
    aggregation_module.Type.COUNT:
    aggregation_module.CountAggregation,
    aggregation_module.Type.DISTRIBUTION:
    aggregation_module.DistributionAggregation,
    aggregation_module.Type.LASTVALUE:
    aggregation_module.LastValueAggregation,
}


def get_metric_type(measure, aggregation):
    """Get the corresponding metric type for the given stats type.

    :type measure: (:class: '~opencensus.stats.measure.BaseMeasure')
    :param measure: the measure for which to find a metric type

    :type aggregation: (:class:
    '~opencensus.stats.aggregation.BaseAggregation')
    :param aggregation: the aggregation for which to find a metric type
    """
    if aggregation.aggregation_type == aggregation_module.Type.NONE:
        raise ValueError("aggregation type must not be NONE")
    assert isinstance(aggregation,
                      AGGREGATION_TYPE_MAP[aggregation.aggregation_type])

    if aggregation.aggregation_type == aggregation_module.Type.SUM:
        if isinstance(measure, measure_module.MeasureInt):
            return metric_descriptor.MetricDescriptorType.CUMULATIVE_INT64
        elif isinstance(measure, measure_module.MeasureFloat):
            return metric_descriptor.MetricDescriptorType.CUMULATIVE_DOUBLE
        else:
            raise ValueError
    elif aggregation.aggregation_type == aggregation_module.Type.COUNT:
        return metric_descriptor.MetricDescriptorType.CUMULATIVE_INT64
    elif aggregation.aggregation_type == aggregation_module.Type.DISTRIBUTION:
        return metric_descriptor.MetricDescriptorType.CUMULATIVE_DISTRIBUTION
    elif aggregation.aggregation_type == aggregation_module.Type.LASTVALUE:
        if isinstance(measure, measure_module.MeasureInt):
            return metric_descriptor.MetricDescriptorType.GAUGE_INT64
        elif isinstance(measure, measure_module.MeasureFloat):
            return metric_descriptor.MetricDescriptorType.GAUGE_DOUBLE
        else:
            raise ValueError
    else:
        raise AssertionError  # pragma: NO COVER


def is_gauge(md_type):
    """Whether a given MetricDescriptorType value is a gauge.

    :type md_type: int
    :param md_type: A MetricDescriptorType enum value.
    """
    if md_type not in metric_descriptor.MetricDescriptorType:
        raise ValueError  # pragma: NO COVER

    return md_type in {
        metric_descriptor.MetricDescriptorType.GAUGE_INT64,
        metric_descriptor.MetricDescriptorType.GAUGE_DOUBLE,
        metric_descriptor.MetricDescriptorType.GAUGE_DISTRIBUTION
    }


def get_label_values(tag_values):
    """Convert an iterable of TagValues into a list of LabelValues.

    :type tag_values: list(:class: `opencensus.tags.tag_value.TagValue`)
    :param tag_values: An iterable of TagValues to convert.

    :rtype: list(:class: `opencensus.metrics.label_value.LabelValue`)
    :return: A list of LabelValues, converted from TagValues.
    """
    return [label_value.LabelValue(tv) for tv in tag_values]


def view_data_to_metric(view_data, timestamp):
    """Convert a ViewData to a Metric at time `timestamp`.

    :type view_data: :class: `opencensus.stats.view_data.ViewData`
    :param view_data: The ViewData to convert.

    :type timestamp: :class: `datetime.datetime`
    :param timestamp: The time to set on the metric's point's aggregation,
    usually the current time.

    :rtype: :class: `opencensus.metrics.export.metric.Metric`
    :return: A converted Metric.
    """
    if not view_data.tag_value_aggregation_data_map:
        return None

    md = view_data.view.get_metric_descriptor()

    # TODO: implement gauges
    if is_gauge(md.type):
        ts_start = None  # pragma: NO COVER
    else:
        ts_start = view_data.start_time

    ts_list = []
    for tag_vals, agg_data in view_data.tag_value_aggregation_data_map.items():
        label_values = get_label_values(tag_vals)
        point = agg_data.to_point(timestamp)
        ts_list.append(time_series.TimeSeries(label_values, [point], ts_start))
    return metric.Metric(md, ts_list)
