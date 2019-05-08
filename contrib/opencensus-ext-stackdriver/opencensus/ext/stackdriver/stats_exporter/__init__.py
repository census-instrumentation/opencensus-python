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

from datetime import datetime
import itertools
import os
import platform
import re
import string
import threading

from google.api_core.gapic_v1 import client_info
from google.cloud import monitoring_v3
import google.auth

from opencensus.common import utils
from opencensus.common.monitored_resource import monitored_resource
from opencensus.common.version import __version__
from opencensus.metrics import label_key
from opencensus.metrics import label_value
from opencensus.metrics import transport
from opencensus.metrics.export import metric as metric_module
from opencensus.metrics.export import metric_descriptor
from opencensus.stats import stats


MAX_TIME_SERIES_PER_UPLOAD = 200
OPENCENSUS_TASK = "opencensus_task"
OPENCENSUS_TASK_DESCRIPTION = "Opencensus task identifier"
DEFAULT_DISPLAY_NAME_PREFIX = "OpenCensus"
ERROR_BLANK_PROJECT_ID = "expecting a non-blank ProjectID"
CONS_NAME = "name"
CONS_TIME_SERIES = "timeseries"
EPOCH_DATETIME = datetime(1970, 1, 1)
EPOCH_PATTERN = "%Y-%m-%dT%H:%M:%S.%fZ"
GLOBAL_RESOURCE_TYPE = 'global'

# OC metric descriptor type to SD metric kind and value type
OC_MD_TO_SD_TYPE = {
    metric_descriptor.MetricDescriptorType.CUMULATIVE_INT64:
    (monitoring_v3.enums.MetricDescriptor.MetricKind.CUMULATIVE,
     monitoring_v3.enums.MetricDescriptor.ValueType.INT64),
    metric_descriptor.MetricDescriptorType.CUMULATIVE_DOUBLE:
    (monitoring_v3.enums.MetricDescriptor.MetricKind.CUMULATIVE,
     monitoring_v3.enums.MetricDescriptor.ValueType.DOUBLE),
    metric_descriptor.MetricDescriptorType.CUMULATIVE_DISTRIBUTION:
    (monitoring_v3.enums.MetricDescriptor.MetricKind.CUMULATIVE,
     monitoring_v3.enums.MetricDescriptor.ValueType.DISTRIBUTION),
    metric_descriptor.MetricDescriptorType.GAUGE_INT64:
    (monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
     monitoring_v3.enums.MetricDescriptor.ValueType.INT64),
    metric_descriptor.MetricDescriptorType.GAUGE_DOUBLE:
    (monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
     monitoring_v3.enums.MetricDescriptor.ValueType.DOUBLE)
}


class Options(object):
    """Exporter configuration options.

     `resource` is an optional field that represents the Stackdriver monitored
     resource type. If unset, this defaults to a `MonitoredResource` with type
     "global" and no resource labels.

     `default_monitoring_labels` are labels added to every metric created by
     this exporter. If unset, this defaults to a single label with key
     "opencensus_task" and value "py-<pid>@<hostname>". This default ensures
     that the set of labels together with the default resource (global) are
     unique to this process, as required by stackdriver.

     If you set `default_monitoring_labels`, make sure that the `resource`
     field together with these labels is unique to the current process. This is
     to ensure that there is only a single writer to each time series in
     Stackdriver.

     Set `default_monitoring_labels` to `{}` to avoid getting the default
     "opencensus_task" label. You should only do this if you know that
     `resource` uniquely identifies this process.

    :type project_id: str
    :param project_id: The ID GCP project to export metrics to, fall back to
        default application credentials if unset.

    :type resource: str
    :param resource: The stackdriver monitored resource type, defaults to
        global.

    :type metric_prefix: str
    :param metric_prefix: Custom prefix for metric name and type.

    :type default_monitoring_labels: dict(
        :class:`opencensus.metrics.label_key.LabelKey`,
        :class:`opencensus.metrics.label_value.LabelValue`)
    :param default_monitoring_labels: Default labels to be set on each exported
        metric.
    """

    def __init__(self,
                 project_id="",
                 resource="",
                 metric_prefix="",
                 default_monitoring_labels=None):
        self.project_id = project_id
        self.resource = resource
        self.metric_prefix = metric_prefix

        if default_monitoring_labels is None:
            self.default_monitoring_labels = {
                label_key.LabelKey(OPENCENSUS_TASK,
                                   OPENCENSUS_TASK_DESCRIPTION):
                label_value.LabelValue(get_task_value())
            }
        else:
            for key, val in default_monitoring_labels.items():
                if not isinstance(key, label_key.LabelKey):
                    raise TypeError
                if not isinstance(val, label_value.LabelValue):
                    raise TypeError
            self.default_monitoring_labels = default_monitoring_labels


class StackdriverStatsExporter(object):
    """Stats exporter for the Stackdriver Monitoring backend."""

    def __init__(self, options=None, client=None):
        if options is None:
            options = Options()
        self._options = options
        self._client = client
        self._md_cache = {}
        self._md_lock = threading.Lock()

    @property
    def options(self):
        return self._options

    @property
    def client(self):
        return self._client

    def export_metrics(self, metrics):
        metrics = list(metrics)
        for metric in metrics:
            self.register_metric_descriptor(metric.descriptor)
        ts_batches = self.create_batched_time_series(metrics)
        for ts_batch in ts_batches:
            self.client.create_time_series(
                self.client.project_path(self.options.project_id), ts_batch)

    def create_batched_time_series(self, metrics,
                                   batch_size=MAX_TIME_SERIES_PER_UPLOAD):
        time_series_list = itertools.chain.from_iterable(
            self.create_time_series_list(metric) for metric in metrics)
        return list(utils.window(time_series_list, batch_size))

    def create_time_series_list(self, metric):
        if not isinstance(metric, metric_module.Metric):  # pragma: NO COVER
            raise ValueError
        return [self._convert_series(metric, ts) for ts in metric.time_series]

    def _convert_series(self, metric, ts):
        """Convert an OC timeseries to a SD series."""
        series = monitoring_v3.types.TimeSeries()
        series.metric.type = self.get_metric_type(metric.descriptor)

        for lk, lv in self.options.default_monitoring_labels.items():
            series.metric.labels[lk.key] = lv.value

        for key, val in zip(metric.descriptor.label_keys, ts.label_values):
            if val.value is not None:
                safe_key = sanitize_label(key.key)
                series.metric.labels[safe_key] = val.value

        set_monitored_resource(series, self.options.resource)

        for point in ts.points:
            sd_point = series.points.add()
            # this just modifies points, no return
            self._convert_point(metric, ts, point, sd_point)
        return series

    def _convert_point(self, metric, ts, point, sd_point):
        """Convert an OC metric point to a SD point."""
        if (metric.descriptor.type == metric_descriptor.MetricDescriptorType
                .CUMULATIVE_DISTRIBUTION):

            sd_dist_val = sd_point.value.distribution_value
            sd_dist_val.count = point.value.count
            sd_dist_val.sum_of_squared_deviation =\
                point.value.sum_of_squared_deviation

            assert sd_dist_val.bucket_options.explicit_buckets.bounds == []
            sd_dist_val.bucket_options.explicit_buckets.bounds.extend(
                [0.0] +
                list(map(float, point.value.bucket_options.type_.bounds))
            )

            assert sd_dist_val.bucket_counts == []
            sd_dist_val.bucket_counts.extend(
                [0] +
                [bb.count for bb in point.value.buckets]
            )

        elif (metric.descriptor.type ==
              metric_descriptor.MetricDescriptorType.CUMULATIVE_INT64):
            sd_point.value.int64_value = int(point.value.value)

        elif (metric.descriptor.type ==
              metric_descriptor.MetricDescriptorType.CUMULATIVE_DOUBLE):
            sd_point.value.double_value = float(point.value.value)

        elif (metric.descriptor.type ==
              metric_descriptor.MetricDescriptorType.GAUGE_INT64):
            sd_point.value.int64_value = int(point.value.value)

        elif (metric.descriptor.type ==
              metric_descriptor.MetricDescriptorType.GAUGE_DOUBLE):
            sd_point.value.double_value = float(point.value.value)

        # TODO: handle SUMMARY metrics, #567
        else:  # pragma: NO COVER
            raise TypeError("Unsupported metric type: {}"
                            .format(metric.descriptor.type))

        end = point.timestamp
        if ts.start_timestamp is None:
            start = end
        else:
            start = datetime.strptime(ts.start_timestamp, EPOCH_PATTERN)

        timestamp_start = (start - EPOCH_DATETIME).total_seconds()
        timestamp_end = (end - EPOCH_DATETIME).total_seconds()

        sd_point.interval.end_time.seconds = int(timestamp_end)

        secs = sd_point.interval.end_time.seconds
        sd_point.interval.end_time.nanos = int((timestamp_end - secs) * 1e9)

        start_time = sd_point.interval.start_time
        start_time.seconds = int(timestamp_start)
        start_time.nanos = int((timestamp_start - start_time.seconds) * 1e9)

    def get_metric_type(self, oc_md):
        """Get a SD metric type for an OC metric descriptor."""
        return namespaced_view_name(oc_md.name, self.options.metric_prefix)

    def get_metric_descriptor(self, oc_md):
        """Convert an OC metric descriptor to a SD metric descriptor."""
        try:
            metric_kind, value_type = OC_MD_TO_SD_TYPE[oc_md.type]
        except KeyError:
            raise TypeError("Unsupported metric type: {}".format(oc_md.type))

        if self.options.metric_prefix:
            display_name_prefix = self.options.metric_prefix
        else:
            display_name_prefix = DEFAULT_DISPLAY_NAME_PREFIX

        desc_labels = new_label_descriptors(
            self.options.default_monitoring_labels, oc_md.label_keys)

        descriptor = monitoring_v3.types.MetricDescriptor(labels=desc_labels)
        metric_type = self.get_metric_type(oc_md)
        descriptor.type = metric_type
        descriptor.metric_kind = metric_kind
        descriptor.value_type = value_type
        descriptor.description = oc_md.description
        descriptor.unit = oc_md.unit
        descriptor.name = ("projects/{}/metricDescriptors/{}"
                           .format(self.options.project_id, metric_type))
        descriptor.display_name = ("{}/{}"
                                   .format(display_name_prefix, oc_md.name))

        return descriptor

    def register_metric_descriptor(self, oc_md):
        """Register a metric descriptor with stackdriver."""
        metric_type = self.get_metric_type(oc_md)
        with self._md_lock:
            if metric_type in self._md_cache:
                return self._md_cache[metric_type]

        descriptor = self.get_metric_descriptor(oc_md)
        project_name = self.client.project_path(self.options.project_id)
        sd_md = self.client.create_metric_descriptor(project_name, descriptor)
        with self._md_lock:
            self._md_cache[metric_type] = sd_md
        return sd_md


def set_monitored_resource(series, option_resource_type):
    """Set a resource(type and labels) that can be used for monitoring.
    :param series: TimeSeries object based on view data
    :param option_resource_type: Resource is an optional field that
    represents the Stackdriver MonitoredResource type.
    """
    resource_type = GLOBAL_RESOURCE_TYPE

    if option_resource_type == "":
        resource = monitored_resource.get_instance()
        if resource is not None:
            resource_labels = resource.get_labels()

            if resource.get_type() == 'gke_container':
                resource_type = 'k8s_container'
                set_attribute_label(series, resource_labels, 'project_id')
                set_attribute_label(series, resource_labels, 'cluster_name')
                set_attribute_label(series, resource_labels, 'container_name')
                set_attribute_label(series, resource_labels, 'namespace_id',
                                    'namespace_name')
                set_attribute_label(series, resource_labels, 'pod_id',
                                    'pod_name')
                set_attribute_label(series, resource_labels, 'zone',
                                    'location')

            elif resource.get_type() == 'gce_instance':
                resource_type = 'gce_instance'
                set_attribute_label(series, resource_labels, 'project_id')
                set_attribute_label(series, resource_labels, 'instance_id')
                set_attribute_label(series, resource_labels, 'zone')

            elif resource.get_type() == 'aws_ec2_instance':
                resource_type = 'aws_ec2_instance'
                set_attribute_label(series, resource_labels, 'aws_account')
                set_attribute_label(series, resource_labels, 'instance_id')
                set_attribute_label(series, resource_labels, 'region',
                                    label_value_prefix='aws:')
    else:
        resource_type = option_resource_type
    series.resource.type = resource_type


def set_attribute_label(series, resource_labels, attribute_key,
                        canonical_key=None, label_value_prefix=''):
    """Set a label to timeseries that can be used for monitoring
    :param series: TimeSeries object based on view data
    :param resource_labels: collection of labels
    :param attribute_key: actual label key
    :param canonical_key: exporter specific label key, Optional
    :param label_value_prefix: exporter specific label value prefix, Optional
    """
    if attribute_key in resource_labels:
        if canonical_key is None:
            canonical_key = attribute_key

        series.resource.labels[canonical_key] = \
            label_value_prefix + resource_labels[attribute_key]


def get_user_agent_slug():
    """Get the UA fragment to identify this library version."""
    return "opencensus-python/{}".format(__version__)


def new_stats_exporter(options=None, interval=None):
    """Get a stats exporter and running transport thread.

    Create a new `StackdriverStatsExporter` with the given options and start
    periodically exporting stats to stackdriver in the background.

    Fall back to default auth if `options` is null. This will raise
    `google.auth.exceptions.DefaultCredentialsError` if default credentials
    aren't configured.

    See `opencensus.metrics.transport.get_exporter_thread` for details on the
    transport thread.

    :type options: :class:`Options`
    :param exporter: Options to pass to the exporter

    :type interval: int or float
    :param interval: Seconds between export calls.

    :rtype: :class:`StackdriverStatsExporter`
    :return: The newly-created exporter.
    """
    if options is None:
        _, project_id = google.auth.default()
        options = Options(project_id=project_id)
    if str(options.project_id).strip() == "":
        raise ValueError(ERROR_BLANK_PROJECT_ID)

    ci = client_info.ClientInfo(client_library_version=get_user_agent_slug())
    client = monitoring_v3.MetricServiceClient(client_info=ci)
    exporter = StackdriverStatsExporter(client=client, options=options)

    transport.get_exporter_thread(stats.stats, exporter, interval=interval)
    return exporter


def get_task_value():
    """ getTaskValue returns a task label value in the format of
     "py-<pid>@<hostname>".
    """
    hostname = platform.uname()[1]
    if not hostname:
        hostname = "localhost"
    return "py-%s@%s" % (os.getpid(), hostname)


def namespaced_view_name(view_name, metric_prefix):
    """ create string to be used as metric type
    """
    metric_prefix = metric_prefix or "custom.googleapis.com/opencensus"
    return os.path.join(metric_prefix, view_name).replace('\\', '/')


def new_label_descriptors(defaults, keys):
    """ create labels for the metric_descriptor
        that will be sent to Stackdriver Monitoring
    """
    label_descriptors = []
    for lk in itertools.chain.from_iterable((defaults.keys(), keys)):
        label = {}
        label["key"] = sanitize_label(lk.key)
        label["description"] = lk.description
        label_descriptors.append(label)

    return label_descriptors


def sanitize_label(text):
    """Remove characters not accepted in labels key

    This replaces any non-word characters (alphanumeric or underscore), with
    an underscore. It also ensures that the first character is a letter by
    prepending with 'key' if necessary, and trims the text to 100 characters.
    """
    if not text:
        return text
    text = re.sub('\\W+', '_', text)
    if text[0] in string.digits:
        text = "key_" + text
    elif text[0] == '_':
        text = "key" + text
    return text[:100]
