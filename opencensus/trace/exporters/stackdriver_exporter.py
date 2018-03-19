# Copyright 2017 Google Inc.
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

from opencensus.trace.attributes import Attributes
from opencensus.trace import attributes_helper
from opencensus.trace.exporters import base
from opencensus.trace.exporters.transports import sync

from google.cloud.trace.client import Client


# OpenCensus Version
VERSION = '0.1.3'

# Agent
AGENT = 'opencensus-python [{}]'.format(VERSION)

# Environment variable set in App Engine when vm:true is set.
_APPENGINE_FLEXIBLE_ENV_VM = 'GAE_APPENGINE_HOSTNAME'

# Environment variable set in App Engine when env:flex is set.
_APPENGINE_FLEXIBLE_ENV_FLEX = 'GAE_INSTANCE'

# GAE common attributes
# See: https://cloud.google.com/appengine/docs/flexible/python/runtime#
#      environment_variables
GAE_ATTRIBUTES = {
    'GAE_FLEX_VERSION': 'g.co/gae/app/version',
    'GAE_FLEX_SERVICE': 'g.co/gae/app/service',
    'GAE_FLEX_PROJECT': 'g.co/gae/app/project',
    'GAE_FLEX_INSTANCE': 'g.co/gae/app/instance',
    'GAE_FLEX_MEMORY_MB': 'g.co/gae/app/memory_mb',
    'GAE_FLEX_PORT': 'g.co/gae/app/port',
}

# GCE common attributes
GCE_ATTRIBUTES = {
    'GCE_INSTANCE_ID': 'g.co/gce/instanceid',
    'GCE_HOSTNAME': 'g.co/gce/hostname',
}


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


class StackdriverExporter(base.Exporter):
    """A exporter that send traces and trace spans to Google Cloud Stackdriver
    Trace.

    :type client: :class: `~google.cloud.trace.client.Client`
    :param client: Stackdriver Trace client.

    :type project_id: str
    :param project_id: project_id to create the Trace client.

    :type transport: :class:`type`
    :param transport: Class for creating new transport objects. It should
                      extend from the base :class:`.Transport` type and
                      implement :meth:`.Transport.export`. Defaults to
                      :class:`.SyncTransport`. The other option is
                      :class:`.BackgroundThreadTransport`.
    """
    def __init__(self, client=None, project_id=None,
                 transport=sync.SyncTransport):
        # The client will handle the case when project_id is None
        if client is None:
            client = Client(project=project_id)

        self.client = client
        self.project_id = client.project
        self.transport = transport(self)

    def emit(self, spans):
        """
        :type spans: dict
        :param spans: Spans collected.
        """
        name = 'projects/{}'.format(self.project_id)
        stackdriver_spans = self.translate_to_stackdriver(spans)
        self.client.batch_write_spans(name, stackdriver_spans)

    def export(self, trace):
        self.transport.export(trace)

    def translate_to_stackdriver(self, spans):
        """Translate the spans json to Stackdriver format.

        See: https://cloud.google.com/trace/docs/reference/v2/rest/v2/
             projects.traces/batchWrite

        :type spans: dict
        :param spans: Spans collected.

        :rtype: dict
        :returns: Spans in Google Cloud StackDriver Trace format.
        """
        set_attributes(spans)
        spans_json = spans.get('spans')
        trace_id = spans.get('traceId')
        spans_list = []

        for span in spans_json:
            span_name = 'projects/{}/traces/{}/spans/{}'.format(
                self.project_id, trace_id, span.get('spanId'))

            span_json = {
                'name': span_name,
                'displayName': span.get('displayName'),
                'startTime': span.get('startTime'),
                'endTime': span.get('endTime'),
                'spanId': str(span.get('spanId')),
                'attributes': span.get('attributes'),
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

            spans_list.append(span_json)

        spans = {'spans': spans_list}
        return spans
