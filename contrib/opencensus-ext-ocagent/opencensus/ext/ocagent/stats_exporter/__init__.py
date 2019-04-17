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

import logging

from google.api_core import bidi
from opencensus.common.monitored_resource import monitored_resource
from opencensus.ext.ocagent import utils
from opencensus.metrics import transport
from opencensus.metrics.export import metric_descriptor
from opencensus.metrics.export import value
from opencensus.proto.agent.metrics.v1 import metrics_service_pb2
from opencensus.proto.agent.metrics.v1 import metrics_service_pb2_grpc
from opencensus.proto.metrics.v1 import metrics_pb2
from opencensus.proto.resource.v1 import resource_pb2
from opencensus.stats import stats
import grpc


class StatsExporter(object):
    """Stats exporter for an opencensus metrics grpc service.

    :type rpc_handler: ExportRpcHandler
    :param rpc_handler: export rpc handler
    """

    def __init__(self, rpc_handler):
        self._rpc_handler = rpc_handler

    def export_metrics(self, metrics):
        """ Exports given metrics to target metric service.
        """
        metric_protos = []
        for metric in metrics:
            metric_protos.append(_get_metric_proto(metric))

        self._rpc_handler.send(
            metrics_service_pb2.ExportMetricsServiceRequest(
                metrics=metric_protos))


def _get_metric_proto(metric):
    return metrics_pb2.Metric(
        metric_descriptor=_get_metric_descriptor_proto(metric.descriptor),
        timeseries=_get_time_series_list_proto(metric.time_series))


def _get_time_series_list_proto(series_list):
    protos = []
    for series in series_list:
        protos.append(
            metrics_pb2.TimeSeries(
                start_timestamp=utils.proto_ts_from_datetime_str(
                    series.start_timestamp),
                label_values=_get_label_values_proto(series.label_values),
                points=_get_points_proto(series.points)))
    return protos


def _get_points_proto(points):
    protos = []
    for point in points:
        proto = metrics_pb2.Point(
            timestamp=utils.proto_ts_from_datetime(point.timestamp))

        if isinstance(point.value, value.ValueLong):
            proto.int64_value = int(point.value.value)
        elif isinstance(point.value, value.ValueDouble):
            proto.double_value = float(point.value.value)
        elif isinstance(point.value, value.ValueDistribution):
            proto.distribution_value.MergeFrom(
                metrics_pb2.DistributionValue(
                    sum=point.value.sum,
                    count=point.value.count,
                    sum_of_squared_deviation=point.value.
                    sum_of_squared_deviation,
                    bucket_options=_get_bucket_options_proto(
                        point.value.bucket_options)
                    if point.value.bucket_options else None,
                    buckets=_get_buckets_proto(point.value.buckets)))

        # TODO: handle SUMMARY metrics, #567
        else:  # pragma: NO COVER
            raise TypeError('Unsupported metric type: {}'.format(
                type(point.value)))
        protos.append(proto)
    return protos


def _get_bucket_options_proto(bucket_options):
    return metrics_pb2.DistributionValue.BucketOptions(
        explicit=metrics_pb2.DistributionValue.BucketOptions.Explicit(
            bounds=bucket_options.type_.bounds))


def _get_buckets_proto(buckets):
    protos = []
    for bucket in buckets:
        protos.append(
            metrics_pb2.DistributionValue.Bucket(
                count=bucket.count,
                exemplar=_get_exemplar_proto(bucket.exemplar)
                if bucket.exemplar else None))
    return protos


def _get_exemplar_proto(exemplar):
    return metrics_pb2.DistributionValue.Exemplar(
        value=exemplar.value,
        timestamp=utils.proto_ts_from_datetime_str(exemplar.timestamp),
        attachments=exemplar.attachments)


def _get_label_values_proto(label_values):
    protos = []
    for label_value in label_values:
        protos.append(
            metrics_pb2.LabelValue(has_value=label_value.value is not None,
                                   value=label_value.value))
    return protos


def _get_metric_descriptor_proto(descriptor):
    return metrics_pb2.MetricDescriptor(
        name=descriptor.name,
        description=descriptor.description,
        unit=descriptor.unit,
        type=_get_metric_descriptor_type_proto(descriptor.type),
        label_keys=_get_label_keys_proto(descriptor.label_keys))


def _get_label_keys_proto(label_keys):
    return [
        metrics_pb2.LabelKey(key=l.key, description=l.description)
        for l in label_keys
    ]


def _get_metric_descriptor_type_proto(descriptor_type):
    return {
        metric_descriptor.MetricDescriptorType.CUMULATIVE_INT64:
        metrics_pb2.MetricDescriptor.CUMULATIVE_INT64,
        metric_descriptor.MetricDescriptorType.CUMULATIVE_DOUBLE:
        metrics_pb2.MetricDescriptor.CUMULATIVE_DOUBLE,
        metric_descriptor.MetricDescriptorType.CUMULATIVE_DISTRIBUTION:
        metrics_pb2.MetricDescriptor.CUMULATIVE_DISTRIBUTION,
        metric_descriptor.MetricDescriptorType.GAUGE_INT64:
        metrics_pb2.MetricDescriptor.GAUGE_INT64,
        metric_descriptor.MetricDescriptorType.GAUGE_DOUBLE:
        metrics_pb2.MetricDescriptor.GAUGE_DOUBLE,
        metric_descriptor.MetricDescriptorType.GAUGE_DISTRIBUTION:
        metrics_pb2.MetricDescriptor.GAUGE_DISTRIBUTION,
        metric_descriptor.MetricDescriptorType.SUMMARY:
        metrics_pb2.MetricDescriptor.SUMMARY,
    }.get(descriptor_type, metrics_pb2.MetricDescriptor.UNSPECIFIED)


class ExportRpcHandler(object):
    """Manages the rpc to the exporter service.

    :type client: class:`~.metrics_service_pb2_grpc.MetricsServiceStub`
    :param client: metrics export client

    :type service_name: str
    :param service_name: name of the service

    :type host_name: str
    :param host_name: name of the host (machine or host name)
    """

    def __init__(self, client, service_name, host_name=None):
        self._initialized = False
        self._initial_request = None
        self._rpc = bidi.BidiRpc(client.Export, lambda: self._initial_request)
        self._node = utils.get_node(service_name, host_name)
        self._resource = _get_resource()

    def send(self, request):
        """Dispatches incoming request on rpc.

        Initializes rpc if necessary and dispatches incoming request.  If a rpc
        error is thrown, this function will attempt to recreate the stream and
        retry sending given request once.

        :type request: class:
          `~.metrics_service_pb2.ExportMetricsServiceRequest`
        :param request: incoming export request
        """
        if not self._initialized:
            self._initialize(request)
            return

        try:
            self._rpc.send(request)
        except grpc.RpcError as e:
            logging.info('Found rpc error %s', e, exc_info=True)
            # If stream has closed due to error, attempt to reopen with the
            # incoming request.
            self._initialize(request)

    def _initialize(self, request):
        """Initializes the exporter rpc stream."""

        # Add node information on the first request dispatched on a stream.
        request.node.MergeFrom(self._node)
        request.resource.MergeFrom(self._resource)
        self._initial_request = request

        self._rpc.open()
        self._initialized = True


def _get_resource():
    instance = monitored_resource.get_instance()

    if instance is not None:
        return resource_pb2.Resource(type=instance.get_type(),
                                     labels=instance.get_labels())
    return resource_pb2.Resource(type='global')


def _create_stub(endpoint):
    return metrics_service_pb2_grpc.MetricsServiceStub(
        grpc.insecure_channel(endpoint))


def new_stats_exporter(service_name,
                       hostname=None,
                       endpoint=None,
                       interval=None):
    """Create a new worker thread and attach the exporter to it.

    :type endpoint: str
    :param endpoint: address of the opencensus service.

    :type service_name: str
    :param service_name: name of the service

    :type host_name: str
    :param host_name: name of the host (machine or host name)

    :type interval: int or float
    :param interval: Seconds between export calls.
    """
    endpoint = utils.DEFAULT_ENDPOINT if endpoint is None else endpoint
    exporter = StatsExporter(
        ExportRpcHandler(_create_stub(endpoint), service_name, hostname))

    transport.get_exporter_thread(stats.stats, exporter, interval)
    return exporter
