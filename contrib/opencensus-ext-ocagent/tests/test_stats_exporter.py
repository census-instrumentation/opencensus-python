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

from concurrent import futures
from datetime import datetime
import grpc
import mock
import os
import socket
import threading
import time
import unittest

from google.protobuf import timestamp_pb2
from opencensus.common import resource
from opencensus.common import utils
from opencensus.common.version import __version__ as opencensus_version
from opencensus.ext.ocagent import stats_exporter as ocagent
from opencensus.metrics import label_value
from opencensus.metrics.export import metric
from opencensus.metrics.export import metric_descriptor
from opencensus.metrics.export import point
from opencensus.metrics.export import time_series
from opencensus.metrics.export import value
from opencensus.proto.agent.common.v1 import common_pb2
from opencensus.proto.agent.metrics.v1 import metrics_service_pb2
from opencensus.proto.agent.metrics.v1 import metrics_service_pb2_grpc
from opencensus.proto.metrics.v1 import metrics_pb2
from opencensus.proto.resource.v1 import resource_pb2
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import metric_utils
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.stats import view_data as view_data_module
from opencensus.tags import tag_key as tag_key_module
from opencensus.tags import tag_map as tag_map_module

SERVICE_NAME = 'my-service'

MiB = 1 << 20
FRONTEND_KEY = tag_key_module.TagKey("my.org/keys/frontend")
FRONTEND_KEY_FLOAT = tag_key_module.TagKey("my.org/keys/frontend-FLOAT")
FRONTEND_KEY_INT = tag_key_module.TagKey("my.org/keys/frontend-INT")
FRONTEND_KEY_STR = tag_key_module.TagKey("my.org/keys/frontend-STR")

FRONTEND_KEY_CLEAN = "my_org_keys_frontend"
FRONTEND_KEY_FLOAT_CLEAN = "my_org_keys_frontend_FLOAT"
FRONTEND_KEY_INT_CLEAN = "my_org_keys_frontend_INT"
FRONTEND_KEY_STR_CLEAN = "my_org_keys_frontend_STR"

VIDEO_SIZE_MEASURE = measure_module.MeasureFloat(
    "my.org/measure/video_size_test2", "size of processed videos", "By")
VIDEO_SIZE_MEASURE_2 = measure_module.MeasureFloat(
    "my.org/measure/video_size_test_2", "size of processed videos", "By")

VIDEO_SIZE_MEASURE_FLOAT = measure_module.MeasureFloat(
    "my.org/measure/video_size_test-float", "size of processed videos-float",
    "By")

VIDEO_SIZE_VIEW_NAME = "my.org/views/video_size_test2"
VIDEO_SIZE_DISTRIBUTION = aggregation_module.DistributionAggregation(
    [16.0 * MiB, 256.0 * MiB])
VIDEO_SIZE_VIEW = view_module.View(VIDEO_SIZE_VIEW_NAME,
                                   "processed video size over time",
                                   [FRONTEND_KEY], VIDEO_SIZE_MEASURE,
                                   VIDEO_SIZE_DISTRIBUTION)

TEST_TIME = datetime(2018, 12, 25, 1, 2, 3, 4)
TEST_TIME_STR = utils.to_iso_str(TEST_TIME)


class TestStatsExporter(unittest.TestCase):
    def test_export_view_data(self):
        v_data = view_data_module.ViewData(view=VIDEO_SIZE_VIEW,
                                           start_time=TEST_TIME_STR,
                                           end_time=TEST_TIME_STR)
        v_data.record(context=tag_map_module.TagMap(), value=2, timestamp=None)
        view_data = [v_data]
        view_data = [metric_utils.view_data_to_metric(view_data[0], TEST_TIME)]

        handler = mock.Mock(spec=ocagent.ExportRpcHandler)
        ocagent.StatsExporter(handler).export_metrics(view_data)

        self.assertEqual(
            handler.send.call_args[0][0].metrics[0].metric_descriptor,
            metrics_pb2.MetricDescriptor(
                name=VIDEO_SIZE_VIEW_NAME,
                description='processed video size over time',
                unit='By',
                type=metrics_pb2.MetricDescriptor.CUMULATIVE_DISTRIBUTION,
                label_keys=[metrics_pb2.LabelKey(key=FRONTEND_KEY)]))

        self.assertEqual(
            handler.send.call_args[0][0].metrics[0].timeseries[0],
            metrics_pb2.TimeSeries(
                start_timestamp=timestamp_pb2.Timestamp(seconds=1545699723,
                                                        nanos=4000),
                label_values=[metrics_pb2.LabelValue(has_value=False)],
                points=[
                    metrics_pb2.Point(
                        timestamp=timestamp_pb2.Timestamp(seconds=1545699723,
                                                          nanos=4000),
                        distribution_value=metrics_pb2.DistributionValue(
                            sum=2,
                            count=1,
                            bucket_options=metrics_pb2.DistributionValue.
                            BucketOptions(
                                explicit=metrics_pb2.DistributionValue.
                                BucketOptions.Explicit(
                                    bounds=[16.0 * MiB, 256.0 * MiB])),
                            buckets=[
                                metrics_pb2.DistributionValue.Bucket(count=1),
                                metrics_pb2.DistributionValue.Bucket(),
                                metrics_pb2.DistributionValue.Bucket(),
                            ]))
                ]))

    def test_export_with_label_value(self):
        view = view_module.View('', '', [FRONTEND_KEY], VIDEO_SIZE_MEASURE,
                                aggregation_module.SumAggregation())
        v_data = view_data_module.ViewData(view=view,
                                           start_time=TEST_TIME_STR,
                                           end_time=TEST_TIME_STR)
        v_data.record(context=tag_map_module.TagMap({FRONTEND_KEY:
                                                     'test-key'}),
                      value=2.5,
                      timestamp=None)
        view_data = [v_data]
        view_data = [metric_utils.view_data_to_metric(view_data[0], TEST_TIME)]

        handler = mock.Mock(spec=ocagent.ExportRpcHandler)
        ocagent.StatsExporter(handler).export_metrics(view_data)
        self.assertEqual(
            handler.send.call_args[0]
            [0].metrics[0].timeseries[0].label_values[0],
            metrics_pb2.LabelValue(has_value=True, value='test-key'))

    def test_export_double_point_value(self):
        view = view_module.View('', '', [FRONTEND_KEY], VIDEO_SIZE_MEASURE,
                                aggregation_module.SumAggregation())
        v_data = view_data_module.ViewData(view=view,
                                           start_time=TEST_TIME_STR,
                                           end_time=TEST_TIME_STR)
        v_data.record(context=tag_map_module.TagMap(),
                      value=2.5,
                      timestamp=None)
        view_data = [v_data]
        view_data = [metric_utils.view_data_to_metric(view_data[0], TEST_TIME)]

        handler = mock.Mock(spec=ocagent.ExportRpcHandler)
        ocagent.StatsExporter(handler).export_metrics(view_data)
        self.assertEqual(
            handler.send.call_args[0]
            [0].metrics[0].timeseries[0].points[0].double_value, 2.5)

    def test_export_exemplar(self):
        metric = _create_metric(
            metric_descriptor.MetricDescriptorType.CUMULATIVE_DISTRIBUTION,
            points=[
                point.Point(value=_create_distribution_value(
                    bounds=[1],
                    buckets=[
                        value.Bucket(count=1,
                                     exemplar=value.Exemplar(
                                         value=2.5,
                                         timestamp=TEST_TIME_STR,
                                         attachments={'key1': 'value1'})),
                        value.Bucket(count=0),
                    ]),
                            timestamp=datetime.now())
            ])

        handler = mock.Mock(spec=ocagent.ExportRpcHandler)
        ocagent.StatsExporter(handler).export_metrics([metric])

        self.assertEqual(
            handler.send.call_args[0][0].metrics[0].timeseries[0].points[0].
            distribution_value.buckets[0].exemplar,
            metrics_pb2.DistributionValue.Exemplar(
                value=2.5,
                timestamp=timestamp_pb2.Timestamp(seconds=1545699723,
                                                  nanos=4000),
                attachments={'key1': 'value1'}))


def _create_distribution_value(count=1,
                               sum_=0,
                               sum_of_squared_deviation=0,
                               bounds=[],
                               buckets=[]):
    return value.ValueDistribution(
        count=count,
        sum_=sum_,
        sum_of_squared_deviation=sum_of_squared_deviation,
        bucket_options=value.BucketOptions(type_=value.Explicit(
            bounds=bounds)),
        buckets=buckets)


def _create_metric(descriptor_type=metric_descriptor.MetricDescriptorType.
                   CUMULATIVE_INT64,
                   points=[]):
    return metric.Metric(
        metric_descriptor.MetricDescriptor('', '', '', descriptor_type, []), [
            time_series.TimeSeries([label_value.LabelValue()], points,
                                   TEST_TIME_STR)
        ])


class GenericRpcHandler(metrics_service_pb2_grpc.MetricsServiceServicer):
    def __init__(self, func):
        self._func = func

    def Export(self, request_iterator, context):
        return self._func(request_iterator, context)


class TestExportRpcInterface(unittest.TestCase):
    def setUp(self):
        self._server = _start_server()
        self._port = self._server.add_insecure_port('[::]:0')
        self._channel = grpc.insecure_channel('localhost:%d' % self._port)

    def tearDown(self):
        self._server.stop(None)
        self._channel.close()

    def _create_stub(self):
        return metrics_service_pb2_grpc.MetricsServiceStub(
            channel=self._channel)

    def _add_and_start_service(self, service):
        metrics_service_pb2_grpc.add_MetricsServiceServicer_to_server(
            service, self._server)
        self._server.start()

    def test_rpc_handler_initialization(self):
        requests = []
        event = threading.Event()

        def _helper(request_iterator, context):
            for request in request_iterator:
                requests.append(request)
                event.set()
            yield

        self._add_and_start_service(GenericRpcHandler(_helper))

        request = metrics_service_pb2.ExportMetricsServiceRequest(
            node=common_pb2.Node(service_info=common_pb2.ServiceInfo(
                name='test-service')))
        _create_rpc_handler(self._create_stub()).send(request)

        self.assertTrue(event.wait(timeout=1))
        self.assertListEqual(requests, [request])

    def test_rpc_handler_export_multiple_packets(self):
        requests = []

        event = threading.Event()

        def _helper(request_iterator, context):
            # Ensure a stream has not been started before accepting a request.
            if len(requests) != 0:
                return

            for request in request_iterator:
                requests.append(request)
                if len(requests) == 2:
                    event.set()
            yield

        self._add_and_start_service(GenericRpcHandler(_helper))

        r1 = metrics_service_pb2.ExportMetricsServiceRequest(
            node=common_pb2.Node(service_info=common_pb2.ServiceInfo(
                name='request1')))
        r2 = metrics_service_pb2.ExportMetricsServiceRequest(
            node=common_pb2.Node(service_info=common_pb2.ServiceInfo(
                name='request2')))

        handler = _create_rpc_handler(self._create_stub())
        handler.send(r1)
        handler.send(r2)

        self.assertTrue(event.wait(timeout=1))
        self.assertListEqual(requests, [r1, r2])

    def test_rpc_handler_stream_restart_on_error(self):
        initialized = []
        requests = []

        event = threading.Event()

        def _helper(request_iterator, context):
            initialized.append(True)
            for request in request_iterator:
                requests.append(request)
                if len(requests) == 2:
                    event.set()
                context.abort(grpc.StatusCode.INTERNAL, '')

        self._add_and_start_service(GenericRpcHandler(_helper))

        request = metrics_service_pb2.ExportMetricsServiceRequest()
        handler = _create_rpc_handler(self._create_stub())

        handler.send(request)
        # Give server time to propagate failure to client
        time.sleep(0.1)
        handler.send(request)

        self.assertTrue(event.wait(timeout=1))
        self.assertEqual(len(initialized), 2)
        self.assertEqual(len(requests), 2)

    @mock.patch('opencensus.metrics.transport.get_exporter_thread')
    def test_create_stats_exporter_initialization(self, mock_transport):
        event = threading.Event()

        def _helper(request_iterator, context):
            for request in request_iterator:
                event.set()
            yield

        self._add_and_start_service(GenericRpcHandler(_helper))

        exporter = ocagent.new_stats_exporter(SERVICE_NAME,
                                              endpoint='localhost:%s' %
                                              self._port,
                                              interval=0.1)

        self.assertEqual(mock_transport.call_args[0][0][0], stats_module.stats)
        self.assertEqual(mock_transport.call_args[0][1], exporter)
        self.assertEqual(mock_transport.call_args[0][2], 0.1)

        exporter.export_metrics([
            _create_metric(points=[
                point.Point(value.ValueLong(1), timestamp=datetime.now())
            ])
        ])
        self.assertTrue(event.wait(timeout=1))

    @mock.patch('opencensus.metrics.transport.get_exporter_thread')
    @mock.patch('grpc.insecure_channel')
    def test_create_stats_exporter_with_default_endpoint(
            self, mock_channel, _):
        ocagent.new_stats_exporter(SERVICE_NAME)
        self.assertEqual(mock_channel.call_args[0][0], 'localhost:55678')

    def test_export_node(self):
        requests = []
        event = threading.Event()

        def _helper(request_iterator, context):
            for request in request_iterator:
                requests.append(request)
                event.set()
            yield

        self._add_and_start_service(GenericRpcHandler(_helper))

        _create_rpc_handler(
            self._create_stub(), service_name=SERVICE_NAME).send(
                metrics_service_pb2.ExportMetricsServiceRequest())

        self.assertTrue(event.wait(timeout=1))
        request = requests[0]
        self.assertEqual(request.node.service_info.name, SERVICE_NAME)
        self.assertEqual(request.node.library_info.language, 8)
        self.assertIsNotNone(request.node.library_info.exporter_version)
        self.assertEqual(request.node.library_info.core_library_version,
                         opencensus_version)

        self.assertEqual(request.node.identifier.host_name,
                         socket.gethostname())
        self.assertEqual(request.node.identifier.pid, os.getpid())

        self.assertIsNotNone(request.node.identifier.start_timestamp)
        self.assertGreater(request.node.identifier.start_timestamp.seconds, 0)

    def test_export_node_with_hostname(self):
        requests = []
        event = threading.Event()

        def _helper(request_iterator, context):
            for request in request_iterator:
                requests.append(request)
                event.set()
            yield

        self._add_and_start_service(GenericRpcHandler(_helper))

        ocagent.ExportRpcHandler(
            self._create_stub(),
            service_name=SERVICE_NAME,
            host_name='my host').send(
                metrics_service_pb2.ExportMetricsServiceRequest())
        self.assertTrue(event.wait(timeout=1))
        self.assertEqual(requests[0].node.identifier.host_name, 'my host')

    @mock.patch(
        'opencensus.common.monitored_resource.monitored_resource.get_instance')
    def test_export_with_resource(self, mock_get_instance):
        event = threading.Event()
        requests = []

        def _helper(request_iterator, context):
            for r in request_iterator:
                requests.append(r)
                event.set()
            yield

        self._add_and_start_service(GenericRpcHandler(_helper))

        mock_get_instance.return_value = resource.Resource(
            type_='gce_instance', labels={'key1': 'value1'})

        _create_rpc_handler(self._create_stub()).send(
            metrics_service_pb2.ExportMetricsServiceRequest())

        self.assertTrue(event.wait(timeout=1))
        self.assertEqual(
            requests[0].resource,
            resource_pb2.Resource(type='gce_instance',
                                  labels={'key1': 'value1'}))

    @mock.patch(
        'opencensus.common.monitored_resource.monitored_resource.get_instance')
    def test_export_with_no_resource_found(self, mock_get_instance):
        event = threading.Event()
        requests = []

        def _helper(request_iterator, context):
            for r in request_iterator:
                requests.append(r)
                event.set()
            yield

        self._add_and_start_service(GenericRpcHandler(_helper))

        mock_get_instance.return_value = None

        _create_rpc_handler(self._create_stub()).send(
            metrics_service_pb2.ExportMetricsServiceRequest())

        self.assertTrue(event.wait(timeout=1))
        self.assertEqual(requests[0].resource,
                         resource_pb2.Resource(type='global'))


def _start_server():
    """Starts an insecure grpc server."""
    return grpc.server(futures.ThreadPoolExecutor(max_workers=1),
                       options=(('grpc.so_reuseport', 0), ))


def _create_rpc_handler(stub, service_name=SERVICE_NAME):
    return ocagent.ExportRpcHandler(stub, SERVICE_NAME)
