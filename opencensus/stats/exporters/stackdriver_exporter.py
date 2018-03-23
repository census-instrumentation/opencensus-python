import os
from google.cloud import monitoring
from google.cloud.monitoring import Client
from google.cloud.monitoring import Metric
from google.cloud.monitoring import MetricDescriptor
from google.cloud.monitoring import MetricKind, ValueType
from google.cloud.monitoring import LabelValueType
from google.cloud.monitoring import LabelDescriptor
from google.cloud.monitoring import Resource
from opencensus.stats import view

class StackDriverExporter(object):
    def __init__(self, client=None, project_id=None, resource=None):
        if client is None:
            client = Client(project=project_id)

        self.client = client
        self.project_id = client.project
        self.resource = client.resource('global', {})

    def emit(self, views, datapoint=None):
        name = 'projects/{}'.format(self.project_id)
        '''metric = {}'''
        self.resource = self.set_resource(type_='global', labels= {'project_id': self.project_id})
        metrics = self.translate_to_stackdriver(views)
        for type, label in metrics:
            metric = self.client.metric(type, label)
            descriptor = self.client.metric_descriptor(type, monitoring.MetricKind.CUMULATIVE, monitoring.ValueType.DISTRIBUTION, description=label)
            descriptor.create()
            if datapoint is not None:
                self.client.write_point(metric, self.resource, datapoint)
                return self.client.time_series(metric, self.resource, datapoint)

    def set_resource(self, type_, labels):
        return self.client.resource(type_, labels)

    def translate_to_stackdriver(self, views):
        metrics = {}
        labels = []
        for v in views or []:
            metric_type = v.View.name
            metric_label = v.view.get_description()
            metrics[metric_type] = metric_label
            labels.append(metric_label)
        return metrics










