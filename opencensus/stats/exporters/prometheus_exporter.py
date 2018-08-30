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

import copy
from prometheus_client import start_http_server
from prometheus_client.core import CollectorRegistry
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.core import CounterMetricFamily
from prometheus_client.core import UntypedMetricFamily
from prometheus_client.core import HistogramMetricFamily
from opencensus.stats.exporters import base
from opencensus.stats import aggregation_data as aggregation_data_module
from opencensus.common.transports import sync


class Options(object):
    """ Options contains options for configuring the exporter.
    """
    def __init__(self,
                 namespace,
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
    """ Collector representes the Prometheus Collector object
    """
    def __init__(self, options=Options(), view_data={}):
        self._options = options
        self._registry = options.registry
        self._view_data = view_data
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
    def view_data(self):
        """ Map with all view data objects
        that will be sent to Prometheus
        """
        return self._view_data

    @property
    def registered_views(self):
        """ Map with all registered views
        """
        return self._registered_views

    def register_views(self, views):
        """ register_views will create the needed structure
        in order to be able to sent all data to Prometheus
        """
        count = 0
        for view in views:
            signature = view_signature(self.options.namespace, view)

            if signature not in self.registered_views:
                desc = {'name': view_name(self.options.namespace, view),
                        'documentation': view.description,
                        'labels': tag_keys_to_labels(view.columns)}
                self.registered_views[signature] = desc
                count += 1

        if count == 0:
            return

        self.registry.register(self)

    def add_view_data(self, view_data):
        """ Add view data object to be sent to server
        """
        self.register_views(view_data.view)
        signature = view_signature(self.options.namespace, view_data.view)
        self.view_data[signature] = view_data

    def to_metric(self, desc, view, tag_map, tag_value_aggregation_map):
        """ to_metric translate the data that OpenCensus create
        to Prometheus format, using Prometheus Metric object
        """
        agg_data = view.aggregation.aggregation_data
        if agg_data is aggregation_data_module.CountAggregationData:
            return CounterMetricFamily(name=desc['name'],
                                       documentation=desc['documentation'],
                                       value=float(agg_data.count_data),
                                       labels=tag_values(tag_map.map))
        elif agg_data is aggregation_data_module.DistributionAggregationData:
            points = {}
            # Histograms are cumulative in Prometheus.
            # 1. Sort buckets in ascending order but, retain
            # their indices for reverse lookup later on.
            # TODO: If there is a guarantee that distribution elements
            # are always sorted, then skip the sorting.
            indices_map = {}
            buckets = []
            for idx, boundarie in view.aggregation.boundaries.boundaries:
                if boundarie not in indices_map:
                    indices_map[boundarie] = idx
                    buckets.append(boundarie)

            buckets.sort()

            # 2. Now that the buckets are sorted by magnitude
            # we can create cumulative indicesmap them back by reverse index
            cum_count = 0
            for bucket in buckets:
                i = indices_map[bucket]
                cum_count += int(agg_data.counts_per_bucket[i])
                points[bucket] = cum_count

            return HistogramMetricFamily(name=desc['name'],
                                         documentation=desc['description'],
                                         buckets=points,
                                         sum_value=agg_data.sum,
                                         labels=tag_values(tag_map.map))

        elif agg_data is aggregation_data_module.SumAggregationDataFloat:
            return UntypedMetricFamily(name=desc['name'],
                                       documentation=desc['description'],
                                       value=agg_data.sum_data,
                                       labels=tag_values(tag_map.map))

        elif agg_data is aggregation_data_module.LastValueAggregationData:
            return GaugeMetricFamily(name=desc['name'],
                                     documentation=desc['description'],
                                     value=agg_data.value,
                                     labels=tag_values(tag_map.map))

        else:
            raise ValueError("unsupported aggregation type %s"
                             % type(agg_data))

    def collect(self):
        """	Collect fetches the statistics from OpenCensus
        and delivers them as Prometheus Metrics.
        Collect is invoked everytime a prometheus.Gatherer is run
        for example when the HTTP endpoint is invoked by Prometheus.
        """
        # We need a copy of all the view data up until this point.
        view_data = copy.deepcopy(self.view_data)

        for v_data in view_data:
            signature = view_signature(self.options.namespace, v_data.view)
            desc = self.registered_views[signature]
            metric = self.to_metric(desc,
                                    v_data.view,
                                    v_data.tag_map,
                                    v_data.tag_value_aggregation_map)
            yield metric

    def describe(self):
        """ describe will be used by Prometheus Client
        to retrieve all registered views.
        """
        registered = {}
        for sign, desc in self.registered_views:
            registered[sign] = desc

        for desc in registered:
            yield desc


class PrometheusStatsExporter(base.StatsExporter):
    """ Exporter exports stats to Prometheus, users need
        to register the exporter as an HTTP Handler to be
        able to export.
    """
    def __init__(self,
                 options,
                 gatherer,
                 transport=sync.SyncTransport,
                 collector=Collector()):
        self._options = options
        self._gatherer = gatherer
        self._collector = collector
        self._transport = transport

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
        if view_data:
            self.transport.export(view_data)

    def on_register_view(self, view):
        return NotImplementedError("Not supported by Prometheus")

    def emit(self, view_data):
        """ Emit exports to the Prometheus if view data has one or more rows.
        Each OpenCensus AggregationData will be converted to
        corresponding Prometheus Metric: SumData will be converted
        to Untyped Metric, CountData will be a Counter Metric
        DistributionData will be a Histogram Metric.
        """
        if not view_data.tag_value_aggregation_map:
            raise Exception("There is no data to be sent.")
        self.collector.add_view_data(view_data)

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

    if not option.registry:
        option.registry = CollectorRegistry()

    collector = new_collector(option)
    exporter = PrometheusStatsExporter(options=option,
                                       gatherer=option.registry,
                                       collector=collector)
    return exporter


def tag_keys_to_labels(tag_keys):
    """ Translate Tag keys to labels
    """
    labels = []
    for key in tag_keys:
        labels.append(key.name)
    return labels


def new_collector(options):
    """ new_collector should be used
    to create instance of Collector class in order to
    prevent the usage of constructor directly
    """
    return Collector(options=options)


def tag_values(tags):
    """ create an array with Tag values
    """
    values = []
    for tag_key, tag_value in tags.items():
        values.append(tag_value.value)
    return values


def view_name(namespace, view):
    """ create the name for the view
    """
    name = ""
    if namespace != "":
        name = namespace + "_"
    return name + view.name


def view_signature(namespace, view):
    """ create the signature for the view
    """
    sign = view_name(namespace, view)
    for key in view.columns:
        sign += "-" + key.name
    return sign
