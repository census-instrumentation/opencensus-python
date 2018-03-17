import os
from google.cloud.monitoring import Client
from google.cloud.monitoring import Metric
from google.cloud.monitoring import MetricDescriptor
from google.cloud.monitoring import MetricKind, ValueType
from google.cloud.monitoring import LabelValueType
from google.cloud.monitoring import LabelDescriptor
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
        metric_list = {}
        metrics = {}
        labels = []
        for v in views or []:
            metric_type = v.View.name
            metric_label = v.view.get_description()
            metrics[metric_type] = metric_label
            labels.append(LabelDescriptor(metric_type, LabelValueType.STRING, metric_label))
            for metric in metrics:
                metric_descriptor = MetricDescriptor(
                    self.client,
                    metric_type,
                    MetricKind.CUMULATIVE,
                    ValueType.DISTRIBUTION,
                    labels,
                    metric,
                    metric_label,
                    metric_type
                )
                metric_list[metric_type]= metric_descriptor
        return metric_list









