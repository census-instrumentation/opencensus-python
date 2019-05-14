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
import six

from google.cloud.trace.client import Client

from opencensus.common import utils
from opencensus.common.monitored_resource import aws_identity_doc_utils
from opencensus.common.monitored_resource import gcp_metadata_config
from opencensus.common.monitored_resource import k8s_utils
from opencensus.common.monitored_resource import monitored_resource
from opencensus.common.transports import sync
from opencensus.common.version import __version__
from opencensus.trace import attributes_helper
from opencensus.trace import base_exporter
from opencensus.trace import span_data as span_data_module
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
    if resource is None:
        return

    resource_type = resource.get_type()
    resource_labels = resource.get_labels()

    def set_attribute_label(attribute_key, label_key,
                            label_value_prefix=''):
        """Add the attribute to the span attribute map.

        Update the span attribute map (`span['attributes']['attributeMap']`) to
        include a given resource label.
        """
        if attribute_key not in resource_labels:
            return

        pair = {RESOURCE_LABEL % (resource_type, label_key):
                label_value_prefix + resource_labels[attribute_key]
                }
        pair_attrs = (format_attributes_json(Attributes(pair))
                      .get('attributeMap'))

        _update_attr_map(span, pair_attrs)

    if resource_type == 'k8s_container':
        set_attribute_label(gcp_metadata_config.PROJECT_ID_KEY, 'project_id')
        set_attribute_label(k8s_utils.CLUSTER_NAME_KEY, 'cluster_name')
        set_attribute_label(k8s_utils.CONTAINER_NAME_KEY, 'container_name')
        set_attribute_label(k8s_utils.NAMESPACE_NAME_KEY, 'namespace_name')
        set_attribute_label(k8s_utils.POD_NAME_KEY, 'pod_name')
        set_attribute_label(gcp_metadata_config.ZONE_KEY, 'location')

    elif resource_type == 'gce_instance':
        set_attribute_label(gcp_metadata_config.PROJECT_ID_KEY, 'project_id')
        set_attribute_label(gcp_metadata_config.INSTANCE_ID_KEY, 'instance_id')
        set_attribute_label(gcp_metadata_config.ZONE_KEY, 'zone')

    elif resource_type == 'aws_ec2_instance':
        set_attribute_label(aws_identity_doc_utils.ACCOUNT_ID_KEY,
                            'aws_account')
        set_attribute_label(aws_identity_doc_utils.INSTANCE_ID_KEY,
                            'instance_id')
        set_attribute_label(aws_identity_doc_utils.REGION_KEY, 'region',
                            label_value_prefix='aws:')


def set_common_attributes(span):
    """Set the common attributes."""
    common = {
        attributes_helper.COMMON_ATTRIBUTES.get('AGENT'): AGENT,
    }
    common_attrs = (format_attributes_json(Attributes(common))
                    .get('attributeMap'))

    _update_attr_map(span, common_attrs)


def set_gae_attributes(span):
    """Set the GAE environment common attributes."""
    for env_var, attribute_key in GAE_ATTRIBUTES.items():
        attribute_value = os.environ.get(env_var)

        if attribute_value is not None:
            pair = {attribute_key: attribute_value}
            pair_attrs = (format_attributes_json(Attributes(pair))
                          .get('attributeMap'))

            _update_attr_map(span, pair_attrs)


def is_gae_environment():
    """Return True if the GAE related env vars is detected."""
    if (_APPENGINE_FLEXIBLE_ENV_VM in os.environ or
            _APPENGINE_FLEXIBLE_ENV_FLEX in os.environ):
        return True
    return False


def format_annotation_json(annotation):
    """Format an Annotation for use by stackdriver.

    :type annotation: :class:`opencensus.trace.time_event.Annotation`
    :param points: The Annotation to format.
    """
    data = {}
    data['description'] = utils.get_truncatable_str(annotation.description)

    if annotation.attributes is not None:
        data['attributes'] = annotation.attributes.format_attributes_json()

    return data


def format_message_event_json(message_event):
    """Format a MessageEvent for use by stackdriver.

    :type message_event: :class:`opencensus.trace.time_event.MessageEvent`
    :param points: The MessageEvent to format.
    """
    data = {}
    data['id'] = message_event.id
    data['type'] = message_event.type

    if message_event.uncompressed_size_bytes is not None:
        data['uncompressed_size_bytes'] = message_event.uncompressed_size_bytes

    if message_event.compressed_size_bytes is not None:
        data['compressed_size_bytes'] = message_event.compressed_size_bytes

    return data


def _format_attribute_value(value):
    if isinstance(value, bool):
        value_type = 'bool_value'
    elif isinstance(value, int):
        value_type = 'int_value'
    elif isinstance(value, six.string_types):
        value_type = 'string_value'
        value = utils.get_truncatable_str(value)
    elif isinstance(value, float):
        value_type = 'double_value'
    else:
        return None

    return {value_type: value}


def format_attributes_json(attributes):
    """Format an Attributes object for use by stackdriver.

    :type message_event: :class:`opencensus.trace.time_event.MessageEvent`
    :param points: The MessageEvent to format.
    """
    attributes_json = {}

    for key, value in attributes.attributes.items():
        key = utils.check_str_length(key)[0]
        value = _format_attribute_value(value)

        if value is not None:
            attributes_json[key] = value

    result = {
        'attributeMap': attributes_json
    }

    return result


def _format_legacy_span_json(span_data):
    """
    :param SpanData span_data: SpanData object to convert
    :rtype: dict
    :return: Dictionary representing the Span
    """
    span_json = {
        'displayName': utils.get_truncatable_str(span_data.name),
        'spanId': span_data.span_id,
        'startTime': span_data.start_time,
        'endTime': span_data.end_time,
        'childSpanCount': span_data.child_span_count,
        'kind': span_data.span_kind
    }

    if span_data.parent_span_id is not None:
        span_json['parentSpanId'] = span_data.parent_span_id

    if span_data.attributes:
        span_json['attributes'] = span_data.attributes.format_attributes_json()

    if span_data.stack_trace is not None:
        span_json['stackTrace'] =\
            span_data.stack_trace.format_stack_trace_json()

    formatted_time_events = []
    if span_data.annotations:
        formatted_time_events.extend(
            {'time': aa.timestamp,
             'annotation': format_annotation_json(aa)}
            for aa in span_data.annotations)
    if span_data.message_events:
        formatted_time_events.extend(
            {'time': me.timestamp,
             'messageEvent': format_message_event_json(me)}
            for me in span_data.message_events)
    if formatted_time_events:
        span_json['timeEvents'] = {
            'timeEvent': formatted_time_events
        }

    if span_data.links:
        span_json['links'] = {
            'link': [
                link.format_link_json() for link in span_data.links]
        }

    if span_data.status is not None:
        span_json['status'] = span_data.status.format_status_json()

    if span_data.same_process_as_parent_span is not None:
        span_json['sameProcessAsParentSpan'] = \
            span_data.same_process_as_parent_span

    return span_json


def format_legacy_trace_json(span_datas):
    """Formats a list of SpanData tuples into the legacy 'trace' dictionary
    format for backwards compatibility
    :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
    :param list of opencensus.trace.span_data.SpanData span_datas:
        SpanData tuples to emit
    :rtype: dict
    :return: Legacy 'trace' dictionary representing given SpanData tuples
    """
    if not span_datas:
        return {}
    top_span = span_datas[0]
    assert isinstance(top_span, span_data_module.SpanData)
    trace_id = top_span.context.trace_id if top_span.context is not None \
        else None
    assert trace_id is not None
    return {
        'traceId': trace_id,
        'spans': [_format_legacy_span_json(sd) for sd in span_datas],
    }


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
            trace = format_legacy_trace_json(sds)
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

        See:
        https://cloud.google.com/trace/docs/reference/v2/rest/v2/projects.traces/batchWrite

        :type trace: dict
        :param trace: Trace dictionary

        :rtype: dict
        :returns: Spans in Google Cloud StackDriver Trace format.
        """  # noqa
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
