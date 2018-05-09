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

import os
from google.cloud import monitoring_v3
from opencensus.stats import view
from opencensus.stats.exporters.transports import sync
from datetime import datetime
from datetime import timedelta


class StackDriverExporter(object):
    def __init__(self, client=None, project_id=None, resource=None, transport=sync.SyncTransport):
        if client is None:
            client = monitoring_v3.MetricServiceClient()

        self.client = client
        self.project_id = client.project
        self.resource = client.resource('global', {'project_id': self.project_id})
        self.transport = transport(self)
        self.name = client.project_path('projects/{}'.format(self.project_id))

    def export(self, views):
        self.transport.export(views)

    def emit(self, views, datapoint=None):
        metrics = self.translate_to_stackdriver(views)
        for metric_type, metric_label in metrics.items():
            metric = self.client.metric(metric_type, metric_label)
            descriptor = self.client.metric_descriptor(self.name, metric_type, monitoring_v3.MetricKind.CUMULATIVE, monitoring_v3.ValueType.INT64, description=metric_label)
            descriptor.create()
            self.client.resource = self.set_resource(type_='global', labels= {'project_id': self.project_id})
            self.client.write_point(metric, self.client.resource, datapoint, datetime.utcnow() + timedelta(seconds=60), datetime.utcnow())
            self.client.time_series(metric, self.client.resource, datapoint, datetime.utcnow() + timedelta(seconds=60), datetime.utcnow())
            return 'Successfully wrote time series.'

    def set_resource(self, type_='global', labels=None):
        my_labels = labels or {}
        return self.client.resource(type_, my_labels)

    def translate_to_stackdriver(self, views):
        metrics = {}
        for v in views or []:
            metric_type = v.View.name
            metric_label = v.view.get_description()
            metrics[metric_type] = metric_label
        return metrics
