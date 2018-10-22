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

from opencensus.metrics import label_key
from opencensus.metrics.export import metric_descriptor
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


def view_to_metric_descriptor(view):
    """Get a MetricDescriptor for given view data.

    :type view: (:class: '~opencensus.stats.view.View')
    :param view: the view data to for which to build a metric descriptor
    """
    return metric_descriptor.MetricDescriptor(
        view.name, view.description, view.measure.unit,
        get_metric_type(view.measure, view.aggregation),
        # TODO: add label key description
        [label_key.LabelKey(tk, "") for tk in view.columns])
