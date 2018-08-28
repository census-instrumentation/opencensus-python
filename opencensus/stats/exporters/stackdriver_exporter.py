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

import re
import os
import platform
from . import base
from google.cloud import monitoring_v3
from opencensus.stats import aggregation
from opencensus.stats import measure
from datetime import datetime
# Add here the import for transport class

MAX_TIME_SERIES_PER_UPLOAD = 200
OPENCENSUS_TASK_DESCRIPTION = "Opencensus task identifier"
DEFAULT_DISPLAY_NAME_PREFIX = "OpenCensus"
ERROR_BLANK_PROJECT_ID = "expecting a non-blank ProjectID"
CONS_NAME = "name"
CONS_TIME_SERIES = "timeseries"
EPOCH_DATETIME = datetime(1970, 1, 1)
EPOCH_PATTERN = "%Y-%m-%dT%H:%M:%S.%fZ"


class Options(object):
    """ Options contains options for configuring the exporter.
    """
    def __init__(self,
                 project_id="",
                 resource="",
                 metric_prefix="",
                 default_monitoring_labels=None):
        self._project_id = project_id
        self._resource = resource
        self._metric_prefix = metric_prefix
        self._default_monitoring_labels = default_monitoring_labels

    @property
    def project_id(self):
        """ project_id is the identifier of the Stackdriver
        project the user is uploading the stats data to.
        If not set, this will default to
        your "Application Default Credentials".
        """
        return self._project_id

    @property
    def resource(self):
        """ Resource is an optional field that represents the Stackdriver
        MonitoredResource type, a resource that can be used for monitoring.
        If no custom ResourceDescriptor is set, a default MonitoredResource
        with type global and no resource labels will be used.
        Optional.
        """
        return self._resource

    @property
    def metric_prefix(self):
        """ metric_prefix overrides the
        OpenCensus prefix of a stackdriver metric.
        Optional.
        """
        return self._metric_prefix

    @property
    def default_monitoring_labels(self):
        """ default_monitoring_labels are labels added to
        every metric created by this
        exporter in Stackdriver Monitoring.

        If unset, this defaults to a single label
        with key "opencensus_task" and value "py-<pid>@<hostname>".
        This default ensures that the set of labels together with
        the default Resource (global) are unique to this
        process, as required by Stackdriver Monitoring.

        If you set default_monitoring_labels,
        make sure that the Resource field
        together with these labels is unique to the
        current process. This is to ensure that
        there is only a single writer to
        each TimeSeries in Stackdriver.

        Set this to Labels to avoid getting the
        default "opencensus_task" label.
        You should only do this if you know that
        the Resource you set uniquely identifies this Python process.
        """
        return self._default_monitoring_labels


class StackdriverStatsExporter(base.StatsExporter):
    """ StackdriverStatsExporter exports stats
    to the Stackdriver Monitoring."""
    def __init__(self,
                 options=Options(),
                 client=None,
                 default_labels={}):
        # Add an argument for transport object
        self._options = options
        self._client = client
        # Add here a property for transport object
        self._default_labels = default_labels

    @property
    def options(self):
        return self._options

    @property
    def client(self):
        return self._client

    @property
    def default_labels(self):
        return self._default_labels

    def set_default_labels(self, value):
        self._default_labels = value

    def on_register_view(self, view):
        """ create metric descriptor for the registered view"""
        if view is not None:
            self.create_metric_descriptor(view)

    def emit(self, view_data):
        """ export data to Stackdriver Monitoring"""
        if view_data is not None:
            self.handle_upload(view_data)

    def export(self, view_data):
        """ export data to transport class"""
        if view_data is not None:
            return
        # self.transport.export(view_data)
        # Uncomment this when transport class gets merged to this branch

    def handle_upload(self, view_data):
        """ handle_upload handles uploading a slice of Data
            as well as error handling.
        """
        if view_data is not None:
            self.upload_stats(view_data)

    def upload_stats(self, view_data):
        """ It receives an array of view_data object
            and create time series for each value
        """
        requests = self.make_request(view_data, MAX_TIME_SERIES_PER_UPLOAD)
        for request in requests:
            self.client.create_time_series(request[CONS_NAME],
                                           request[CONS_TIME_SERIES])

    def make_request(self, view_data, limit):
        """ Create the data structure that will be
            sent to Stackdriver Monitoring
        """
        requests = []
        time_series = []

        resource = self.options.resource
        for v_data in view_data:
            series = self.create_time_series_list(v_data, resource)
            time_series.append(series)

            project_id = self.options.project_id
            request = {}
            request[CONS_NAME] = self.client.project_path(project_id)
            request[CONS_TIME_SERIES] = time_series
            requests.append(request)

            if len(time_series) == int(limit):
                time_series = []
        return requests

    def create_time_series_list(self, v_data, resource_type):
        """ Create the TimeSeries object based on the view data
        """
        series = monitoring_v3.types.TimeSeries()
        series.metric.type = namespaced_view_name(v_data.view.name)

        if resource_type is None:
            series.resource.type = 'global'
        else:
            series.resource.type = resource_type

        tag_agg = v_data.tag_value_aggregation_map
        for tag_value, agg in tag_agg.items():
            point = series.points.add()
            if agg.aggregation_type is aggregation.Type.DISTRIBUTION:
                agg_data = tag_agg.get(tag_value).aggregation_data

                dist_value = point.value.distribution_value
                dist_value.count = agg_data.count_data
                dist_value.mean = agg_data.mean_data

                sum_of_sqd = agg_data.sum_of_sqd_deviations
                dist_value.sum_of_squared_deviation = sum_of_sqd

                # Uncomment this when stackdriver supports Range
                # point.value.distribution_value.range.min = agg_data.min
                # point.value.distribution_value.range.max = agg_data.max
                bounds = dist_value.bucket_options.explicit_buckets.bounds
                bounds.extend(list(map(float, agg_data.bounds)))

                buckets = dist_value.bucket_counts
                buckets.extend(list(map(int, agg_data.counts_per_bucket)))
            elif type(tag_value.value) is int:
                point.value.int64_value = int(tag_value.value)
            elif type(tag_value.value) is float:
                point.value.float_value = float(tag_value.value)
            elif type(tag_value.value) is str:
                point.value.string_value = str(tag_value.value)

            start = datetime.strptime(v_data.start_time, EPOCH_PATTERN)
            end = datetime.strptime(v_data.end_time, EPOCH_PATTERN)

            timestamp_start = (start - EPOCH_DATETIME).total_seconds()
            timestamp_end = (end - EPOCH_DATETIME).total_seconds()

            point.interval.end_time.seconds = int(timestamp_end)

            secs = point.interval.end_time.seconds
            point.interval.end_time.nanos = int((timestamp_end-secs)*10**9)

            # Uncomment this when LastValue gets supported
            # sif not agg.aggregation_type is aggregation.Type.LASTVALUE:
            if timestamp_start == timestamp_end:
                # avoiding start_time and end_time to be equal
                timestamp_start = timestamp_start - 1

            start_time = point.interval.start_time
            start_time.seconds = int(timestamp_start)
            start_secs = start_time.seconds
            start_time.nanos = int((timestamp_start - start_secs) * 10**9)
        return series

    def create_metric_descriptor(self, view):
        """ it creates a MetricDescriptor
        for the given view data in Stackdriver Monitoring.
        An error will be raised if there is
        already a metric descriptor created with the same name
        but it has a different aggregation or keys.
        """
        view_measure = view.measure
        view_aggregation = view.aggregation
        view_name = view.name

        metric_type = namespaced_view_name(view_name)
        value_type = None
        unit = view_measure.unit
        metric_desc = monitoring_v3.enums.MetricDescriptor
        agg_type = aggregation.Type

        # Default metric Kind
        metric_kind = metric_desc.MetricKind.CUMULATIVE

        if view_aggregation.aggregation_type is agg_type.COUNT:
            value_type = metric_desc.ValueType.INT64
            # If the aggregation type is count
            # which counts the number of recorded measurements
            # the unit must be "1", because this view
            # does not apply to the recorded values.
            unit = str(1)
        elif view_aggregation.aggregation_type is agg_type.SUM:
            if isinstance(view_measure, measure.MeasureInt):
                value_type = metric_desc.ValueType.INT64
            elif isinstance(view_measure, measure.MeasureFloat):
                value_type = metric_desc.ValueType.DOUBLE
        elif view_aggregation.aggregation_type is agg_type.DISTRIBUTION:
            value_type = metric_desc.ValueType.DISTRIBUTION
        # Aggregation type last value is not
        # currently supported by opencesus python stats
        # elif view_aggregation.aggregation_type is agg_type.LASTVALUE:
        #	metric_kind = metric_desc.MetricKind.GAUGE
        # 	if view_measure is measure.MeasureInt:
        # 		value_type = metric_desc.ValueType.INT64
        # 	elif view_measure is measure.MeasureFloat:
        # 		value_type = metric_desc.ValueType.DOUBLE
        else:
            raise Exception("unsupported aggregation type: %s"
                            % str(view_aggregation.aggregation_type))

        display_name_prefix = DEFAULT_DISPLAY_NAME_PREFIX
        if self.options.metric_prefix != "":
            display_name_prefix = self.options.metric_prefix

        descriptor_pattern = "projects/%s/metricDescriptors/%s"
        project_id = self.options.project_id

        desc_labels = new_label_descriptors(self.default_labels, view.columns)

        descriptor = monitoring_v3.types.MetricDescriptor(labels=desc_labels)
        descriptor.type = metric_type
        descriptor.metric_kind = metric_kind
        descriptor.value_type = value_type
        descriptor.description = view.description
        descriptor.unit = unit

        descriptor.name = descriptor_pattern % (project_id, metric_type)
        descriptor.display_name = "%s/%s" % (display_name_prefix, view_name)

        client = self.client
        project_name = client.project_path(project_id)
        descriptor = client.create_metric_descriptor(project_name, descriptor)


def new_stats_exporter(options):
    """ new_stats_exporter returns an exporter that
        uploads stats data to Stackdriver Monitoring.
    """
    if str(options.project_id).strip() == "":
        raise Exception(ERROR_BLANK_PROJECT_ID)

    client = monitoring_v3.MetricServiceClient()

    exporter = StackdriverStatsExporter(client=client, options=options)

    if options.default_monitoring_labels is not None:
        exporter.set_default_labels(options.default_monitoring_labels)
    else:
        label = {}
        key = remove_non_alphanumeric(get_task_value())
        label[key] = OPENCENSUS_TASK_DESCRIPTION
        exporter.set_default_labels(label)
    return exporter


def get_task_value():
    """ getTaskValue returns a task label value in the format of
     "py-<pid>@<hostname>".
    """
    hostname = platform.uname()[1]
    if hostname is None:
        hostname = "localhost"
    return "py@" + str(os.getpid()) + hostname


def namespaced_view_name(view_name):
    """ create string to be used as metric type
    """
    return os.path.join("custom.googleapis.com", "opencensus", view_name)


def new_label_descriptors(defaults, keys):
    """ create labels for the metric_descriptor
        that will be sent to Stackdriver Monitoring
    """
    label_descriptors = []
    for key, lbl in defaults.items():
        label = {}
        label["key"] = remove_non_alphanumeric(key)
        label["description"] = lbl
        label_descriptors.append(label)

    for tag_key in keys:
        label = {}
        label["key"] = remove_non_alphanumeric(tag_key.name)
        label_descriptors.append(label)
    return label_descriptors


def remove_non_alphanumeric(text):
    """ Remove characters not accepted in labels key
    """
    return str(re.sub('[^0-9a-zA-Z ]+', '', text)).replace(" ", "")
