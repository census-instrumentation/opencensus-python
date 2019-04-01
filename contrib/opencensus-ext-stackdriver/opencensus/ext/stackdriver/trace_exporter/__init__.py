# Copyright 2017, OpenCensus Authors
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

from collections import defaultdict
import os

from google.cloud.trace.client import Client

from opencensus.common.monitored_resource import monitored_resource
from opencensus.common.transports import sync
from opencensus.common.version import __version__
from opencensus.trace import attributes_helper
from opencensus.trace import base_exporter
from opencensus.trace import span_data
from opencensus.trace.attributes import Attributes

# Agent
AGENT = 'opencensus-python [{}]'.format(__version__)

# Environment variable set in App Engine when vm:true is set.
_APPENGINE_FLEXIBLE_ENV_VM = 'GAE_APPENGINE_HOSTNAME'

# Environment variable set in App Engine when env:flex is set.
_APPENGINE_FLEXIBLE_ENV_FLEX = 'GAE_INSTANCE'

# GAE common attributes
# See: https://cloud.google.com/appengine/docs/flexible/python/runtime#
#      environment_variables
GAE_ATTRIBUTES = {
    'GAE_VERSION': 'g.co/gae/app/version',
    # Note that as of June 2018, the GAE_SERVICE variable needs to map
    # to the g.co/gae/app/module attribute in order for the stackdriver
    # UI to properly filter by 'service' - kinda inconsistent...
    'GAE_SERVICE': 'g.co/gae/app/module',
    'GOOGLE_CLOUD_PROJECT': 'g.co/gae/app/project',
    'GAE_INSTANCE': 'g.co/gae/app/instance',
    'GAE_MEMORY_MB': 'g.co/gae/app/memory_mb',
    'PORT': 'g.co/gae/app/port',
}

# resource label structure
RESOURCE_LABEL = 'g.co/r/%s/%s'


def _update_attr_map(span, attrs):
    attr_map = span.get('attributes', {}).get('attributeMap', {})
    attr_map.update(attrs)
    span['attributes']['attributeMap'] = attr_map


def set_attributes(trace):
    """Automatically set attributes for Google Cloud environment."""
    spans = trace.get('spans')
    for span in spans:
        if span.get('attributes') is None:
            span['attributes'] = {}

        if is_gae_environment():
            set_gae_attributes(span)

        set_common_attributes(span)

        set_monitored_resource_attributes(span)


def set_monitored_resource_attributes(span):
    """Set labels to span that can be used for tracing.
    :param span: Span object
    """
    resource = monitored_resource.get_instance()
    if resource is not None:
        resource_type = resource.get_type()
        resource_labels = resource.get_labels()

        if resource_type == 'gke_container':
            resource_type = 'k8s_container'
            set_attribute_label(span, resource_type, resource_labels,
                                'project_id')
            set_attribute_label(span, resource_type, resource_labels,
                                'cluster_name')
            set_attribute_label(span, resource_type, resource_labels,
                                'container_name')
            set_attribute_label(span, resource_type, resource_labels,
                                'namespace_id', 'namespace_name')
            set_attribute_label(span, resource_type, resource_labels,
                                'pod_id', 'pod_name')
            set_attribute_label(span, resource_type, resource_labels,
                                'zone', 'location')

        elif resource_type == 'gce_instance':
            set_attribute_label(span, resource_type, resource_labels,
                                'project_id')
            set_attribute_label(span, resource_type, resource_labels,
                                'instance_id')
            set_attribute_label(span, resource_type, resource_labels,
                                'zone')

        elif resource_type == 'aws_ec2_instance':
            set_attribute_label(span, resource_type, resource_labels,
                                'aws_account')
            set_attribute_label(span, resource_type, resource_labels,
                                'instance_id')
            set_attribute_label(span, resource_type, resource_labels,
                                'region', label_value_prefix='aws:')


def set_attribute_label(span, resource_type, resource_labels, attribute_key,
                        canonical_key=None, label_value_prefix=''):
    """Set a label to span that can be used for tracing.
    :param span: Span object
    :param resource_type: resource type
    :param resource_labels: collection of labels
    :param attribute_key: actual label key
    :param canonical_key: exporter specific label key, Optional
    :param label_value_prefix: exporter specific label value prefix, Optional
    """

    if attribute_key in resource_labels:
        if canonical_key is None:
            canonical_key = attribute_key

        pair = {RESOURCE_LABEL % (resource_type, canonical_key):
                label_value_prefix + resource_labels[attribute_key]
                }
        pair_attrs = Attributes(pair).format_attributes_json()\
            .get('attributeMap')

        _update_attr_map(span, pair_attrs)


def set_common_attributes(span):
    """Set the common attributes."""
    common = {
        attributes_helper.COMMON_ATTRIBUTES.get('AGENT'): AGENT,
    }
    common_attrs = Attributes(common)\
        .format_attributes_json()\
        .get('attributeMap')

    _update_attr_map(span, common_attrs)


def set_gae_attributes(span):
    """Set the GAE environment common attributes."""
    for env_var, attribute_key in GAE_ATTRIBUTES.items():
        attribute_value = os.environ.get(env_var)

        if attribute_value is not None:
            pair = {attribute_key: attribute_value}
            pair_attrs = Attributes(pair)\
                .format_attributes_json()\
                .get('attributeMap')

            _update_attr_map(span, pair_attrs)


def is_gae_environment():
    """Return True if the GAE related env vars is detected."""
    if (_APPENGINE_FLEXIBLE_ENV_VM in os.environ or
            _APPENGINE_FLEXIBLE_ENV_FLEX in os.environ):
        return True


class StackdriverExporter(base_exporter.Exporter):
    """A exporter that send traces and trace spans to Google Cloud Stackdriver
    Trace.

    :type client: :class: `~google.cloud.trace.client.Client`
    :param client: Stackdriver Trace client.

    :type project_id: str
    :param project_id: project_id to create the Trace client.

    :type transport: :class:`type`
    :param transport: Class for creating new transport objects. It should
                      extend from the base_exporter :class:`.Transport` type
                      and implement :meth:`.Transport.export`. Defaults to
                      :class:`.SyncTransport`. The other option is
                      :class:`.AsyncTransport`.
    """

    def __init__(self, client=None, project_id=None,
                 transport=sync.SyncTransport):
        # The client will handle the case when project_id is None
        if client is None:
            client = Client(project=project_id)

        self.client = client
        self.project_id = client.project
        self.transport = transport(self)

    def emit(self, span_datas):
        """
        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param list of opencensus.trace.span_data.SpanData span_datas:
            SpanData tuples to emit
        """
        project = 'projects/{}'.format(self.project_id)

        # Map each span data to it's corresponding trace id
        trace_span_map = defaultdict(list)
        for sd in span_datas:
            trace_span_map[sd.context.trace_id] += [sd]

        stackdriver_spans = []
        # Write spans to Stackdriver
        for _, sds in trace_span_map.items():
            # convert to the legacy trace json for easier refactoring
            # TODO: refactor this to use the span data directly
            trace = span_data.format_legacy_trace_json(sds)
            stackdriver_spans.extend(self.translate_to_stackdriver(trace))

        self.client.batch_write_spans(project, {'spans': stackdriver_spans})

    def export(self, span_datas):
        """
        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param list of opencensus.trace.span_data.SpanData span_datas:
            SpanData tuples to export
        """
        self.transport.export(span_datas)

    def translate_to_stackdriver(self, trace):
        """Translate the spans json to Stackdriver format.

        See: https://cloud.google.com/trace/docs/reference/v2/rest/v2/
             projects.traces/batchWrite

        :type trace: dict
        :param trace: Trace dictionary

        :rtype: dict
        :returns: Spans in Google Cloud StackDriver Trace format.
        """
        set_attributes(trace)
        spans_json = trace.get('spans')
        trace_id = trace.get('traceId')

        for span in spans_json:
            span_name = 'projects/{}/traces/{}/spans/{}'.format(
                self.project_id, trace_id, span.get('spanId'))

            span_json = {
                'name': span_name,
                'displayName': span.get('displayName'),
                'startTime': span.get('startTime'),
                'endTime': span.get('endTime'),
                'spanId': str(span.get('spanId')),
                'attributes': self.map_attributes(span.get('attributes')),
                'links': span.get('links'),
                'status': span.get('status'),
                'stackTrace': span.get('stackTrace'),
                'timeEvents': span.get('timeEvents'),
                'sameProcessAsParentSpan': span.get('sameProcessAsParentSpan'),
                'childSpanCount': span.get('childSpanCount')
            }

            if span.get('parentSpanId') is not None:
                parent_span_id = str(span.get('parentSpanId'))
                span_json['parentSpanId'] = parent_span_id

            yield span_json

    def map_attributes(self, attribute_map):
        if attribute_map is None:
            return attribute_map

        for (key, value) in attribute_map.items():
            if (key != 'attributeMap'):
                continue
            for attribute_key in list(value.keys()):
                if (attribute_key in ATTRIBUTE_MAPPING):
                    new_key = ATTRIBUTE_MAPPING.get(attribute_key)
                    value[new_key] = value.pop(attribute_key)

        return attribute_map


ATTRIBUTE_MAPPING = {
    'component': '/component',
    'error.message': '/error/message',
    'error.name': '/error/name',
    'http.client_city': '/http/client_city',
    'http.client_country': '/http/client_country',
    'http.client_protocol': '/http/client_protocol',
    'http.client_region': '/http/client_region',

    'http.host': '/http/host',
    'http.method': '/http/method',

    'http.redirected_url': '/http/redirected_url',
    'http.request_size': '/http/request/size',
    'http.response_size': '/http/response/size',

    'http.status_code': '/http/status_code',
    'http.url': '/http/url',
    'http.user_agent': '/http/user_agent',

    'pid': '/pid',
    'stacktrace': '/stacktrace',
    'tid': '/tid',

    'grpc.host_port': '/grpc/host_port',
    'grpc.method': '/grpc/method',
}
