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

from prometheus_client import start_http_server
from prometheus_client.core import CollectorRegistry
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.core import CounterMetricFamily
from prometheus_client.core import UntypedMetricFamily
from prometheus_client.core import HistogramMetricFamily
from prometheus_client.core import REGISTRY
from opencensus.stats.exporters import base
from opencensus.stats import aggregation_data as aggregation_data_module
from opencensus.common.transports import sync


class Options(object):
    """ Options contains options for configuring the exporter.
    The address can be empty as the prometheus client will
    assume it's localhost

    :type namespace: str
    :param namespace: The prometheus namespace to be used. Defaults to ''.

    :type port: int
    :param port: The Prometheus port to be used. Defaults to 8000.

    :type address: str
    :param address: The Prometheus address to be used. Defaults to ''.

    :type registry: registry
    :param registry: The Prometheus address to be used. Defaults to ''.

    :type registry: :class:`~prometheus_client.core.CollectorRegistry`
    :param registry: A Prometheus collector registry instance.
    """
    def __init__(self,
                 namespace='',
                 port=8000,
                 address='',
                 registry=CollectorRegistry()):
        self._namespace = namespace
        self._registry = registry
        self._port = int(port)
        self._address = address

    @property
    def registry(self):
        """ Prometheus Collector Registry instance
        """
        return self._registry

    @property
    def namespace(self):
        """ Prefix to be used with view name
        """
        return self._namespace

    @property
    def port(self):
        """ Port number to listen
        """
        return self._port

    @property
    def address(self):
        """ Endpoint address (default is localhost)
        """
        return self._address


class Collector(object):
    """ Collector represents the Prometheus Collector object
    """
    def __init__(self, options=Options(), view_name_to_data_map={}):
        self._options = options
        self._registry = options.registry
        self._view_name_to_data_map = view_name_to_data_map
        self._registered_views = {}

    @property
    def options(self):
        """ Options to be used to configure the exporter
        """
        return self._options

    @property
    def registry(self):
        """ Prometheus Collector Registry instance
        """
        return self._registry

    @property
    def view_name_to_data_map(self):
        """ Map with all view data objects
        that will be sent to Prometheus
        """
        return self._view_name_to_data_map

    @property
    def registered_views(self):
        """ Map with all registered views
        """
        return self._registered_views

    def register_view(self, view):
        """ register_view will create the needed structure
        in order to be able to sent all data to Prometheus
        """
        v_name = view_name(self.options.namespace, view)

        if v_name not in self.registered_views:
            desc = {'name': v_name,
                    'documentation': view.description,
                    'labels': list(view.columns)}
            self.registered_views[v_name] = desc
            self.registry.register(self)

    def add_view_data(self, view_data):
        """ Add view data object to be sent to server
        """
        self.register_view(view_data.view)
        v_name = view_name(self.options.namespace, view_data.view)
        self.view_name_to_data_map[v_name] = view_data

    # TODO: add start and end timestamp
    def to_metric(self, desc, tag_values, agg_data):
        """ to_metric translate the data that OpenCensus create
        to Prometheus format, using Prometheus Metric object

        :type desc: dict
        :param desc: The map that describes view definition

        :type tag_values: tuple of :class:
            `~opencensus.tags.tag_value.TagValue`
        :param object of opencensus.tags.tag_value.TagValue:
            TagValue object used as label values

        :type agg_data: object of :class:
            `~opencensus.stats.aggregation_data.AggregationData`
        :param object of opencensus.stats.aggregation_data.AggregationData:
            Aggregated data that needs to be converted as Prometheus samples

        :rtype: :class:`~prometheus_client.core.CounterMetricFamily` or
                :class:`~prometheus_client.core.HistogramMetricFamily` or
                :class:`~prometheus_client.core.UntypedMetricFamily` or
                :class:`~prometheus_client.core.GaugeMetricFamily`
        :returns: A Prometheus metric object
        """
        metric_name = desc['name']
        metric_description = desc['documentation']
        label_keys = desc['labels']

        metric = None
        if isinstance(agg_data, aggregation_data_module.CountAggregationData):
            metric = CounterMetricFamily(name=metric_name,
                                         documentation=metric_description,
                                         labels=label_keys)
            metric.add_metric(labels=list(tag_values),
                              value=agg_data.count_data)

        elif isinstance(agg_data,
                        aggregation_data_module.DistributionAggregationData):

            assert(agg_data.bounds == sorted(agg_data.bounds))
            points = {}
            cum_count = 0
            for ii, bound in enumerate(agg_data.bounds):
                cum_count += agg_data.counts_per_bucket[ii]
                points[str(bound)] = cum_count
            metric = HistogramMetricFamily(name=metric_name,
                                           documentation=metric_description,
                                           labels=label_keys)
            metric.add_metric(labels=list(tag_values),
                              buckets=list(points.items()),
                              sum_value=agg_data.sum,)

        elif isinstance(agg_data,
                        aggregation_data_module.SumAggregationDataFloat):
            metric = UntypedMetricFamily(name=metric_name,
                                         documentation=metric_description,
                                         labels=label_keys)
            metric.add_metric(labels=list(tag_values),
                              value=agg_data.sum_data)

        elif isinstance(agg_data,
                        aggregation_data_module.LastValueAggregationData):
            metric = GaugeMetricFamily(name=metric_name,
                                       documentation=metric_description,
                                       labels=label_keys)
            metric.add_metric(labels=list(tag_values),
                              value=agg_data.value)

        else:
            raise ValueError("unsupported aggregation type %s"
                             % type(agg_data))

        return metric

    def collect(self):  # pragma: NO COVER
        """Collect fetches the statistics from OpenCensus
        and delivers them as Prometheus Metrics.
        Collect is invoked every time a prometheus.Gatherer is run
        for example when the HTTP endpoint is invoked by Prometheus.
        """
        for v_name in list(self.view_name_to_data_map):
            if v_name not in self.registered_views:
                continue
            desc = self.registered_views[v_name]
            view_data = self.view_name_to_data_map[view_name]
            for tag_values in view_data.tag_value_aggregation_data_map:
                agg_data = view_data.tag_value_aggregation_data_map[tag_values]
                metric = self.to_metric(desc, tag_values, agg_data)
                yield metric


class PrometheusStatsExporter(base.StatsExporter):
    """ Exporter exports stats to Prometheus, users need
        to register the exporter as an HTTP Handler to be
        able to export.

    :type options:
        :class:`~opencensus.stats.exporters.prometheus_exporters.Options`
    :param options: An options object with the parameters to instantiate the
                         prometheus exporter.

    :type gatherer: :class:`~prometheus_client.core.CollectorRegistry`
    :param gatherer: A Prometheus collector registry instance.

    :type transport:
        :class:`opencensus.common.transports.sync.SyncTransport` or
        :class:`opencensus.common.transports.async_.AsyncTransport`
    :param transport: An instance of a Transpor to send data with.

    :type collector:
        :class:`~opencensus.stats.exporters.prometheus_exporters.Collector`
    :param collector: An instance of the Prometheus Collector object.
    """
    def __init__(self,
                 options,
                 gatherer,
                 transport=sync.SyncTransport,
                 collector=Collector()):
        self._options = options
        self._gatherer = gatherer
        self._collector = collector
        self._transport = transport(self)
        self.serve_http()
        REGISTRY.register(self._collector)

    @property
    def transport(self):
        """ The transport way to be sent data to server
        (default is sync).
        """
        return self._transport

    @property
    def collector(self):
        """ Collector class instance to be used
        to communicate with Prometheus
        """
        return self._collector

    @property
    def gatherer(self):
        """ Prometheus Collector Registry instance
        """
        return self._gatherer

    @property
    def options(self):
        """ Options to be used to configure the exporter
        """
        return self._options

    def export(self, view_data):
        """ export send the data to the transport class
        in order to be sent to Prometheus in a sync or async way.
        """
        if view_data is not None:  # pragma: NO COVER
            self.transport.export(view_data)

    def on_register_view(self, view):
        return NotImplementedError("Not supported by Prometheus")

    def emit(self, view_data):  # pragma: NO COVER
        """ Emit exports to the Prometheus if view data has one or more rows.
        Each OpenCensus AggregationData will be converted to
        corresponding Prometheus Metric: SumData will be converted
        to Untyped Metric, CountData will be a Counter Metric
        DistributionData will be a Histogram Metric.
        """

        for v_data in view_data:
            if v_data.tag_value_aggregation_data_map:
                self.collector.add_view_data(v_data)

    def serve_http(self):
        """ serve_http serves the Prometheus endpoint.
        """
        start_http_server(port=self.options.port,
                          addr=str(self.options.address))


def new_stats_exporter(option):
    """ new_stats_exporter returns an exporter
    that exports stats to Prometheus.
    """
    if option.namespace == "":
        raise ValueError("Namespace can not be empty string.")

    collector = new_collector(option)

    exporter = PrometheusStatsExporter(options=option,
                                       gatherer=option.registry,
                                       collector=collector)
    return exporter


def new_collector(options):
    """ new_collector should be used
    to create instance of Collector class in order to
    prevent the usage of constructor directly
    """
    return Collector(options=options)


def view_name(namespace, view):
    """ create the name for the view
    """
    name = ""
    if namespace != "":
        name = namespace + "_"
    return name + view.name
