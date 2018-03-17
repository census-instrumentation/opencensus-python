import os
from google.cloud.monitoring import Client
from google.cloud.monitoring import LabelDescriptor
from google.cloud.monitoring import Metric
from google.cloud.monitoring import MetricKind, ValueType
from opencensus.stats import view

class StackDriverExporter(object):
    def __init__(self, client=None, project_id=None):
        if client is None:
            client = Client(project=project_id)

        self.client = client
        self.project_id = client.project

    def emit(self, metrics):
        ''' finish this up '''


    def translate_to_stackdriver(self, views):
        metric_list = []
        for view in views:
            metric_type = view.get_name()
            metric_label = view.get_description()
            metrics = {metric_type : metric_label}

            for metric in metrics:
                metric_descriptor = {
                    'type': metrics[metric_type],
                    'metricKind': metric['metricKind'],
                    'valueType': metric['valueType'],
                    'labels': metrics.values(),
                    'unit': metric['unit'],
                    'description': metric['description'],
                    'displayName': metric['displayName']
                }

                metric_list.append(metric_descriptor)
        metrics = {metric_type: metric_descriptor}
        return metrics









