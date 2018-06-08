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

from google.cloud.trace.client import Client

from opencensus.trace import attributes_helper
from opencensus.trace.attributes import Attributes
from opencensus.trace.exporters import base
from opencensus.trace.exporters.transports import sync
from opencensus.trace.utils import _get_truncatable_str

# OpenCensus Version
VERSION = '0.1.5'

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


def set_attributes(attr):
    """Automatically set attributes for Google Cloud environment."""
    if is_gae_environment():
        set_gae_attributes(attr)
    set_common_attributes(attr)


def set_common_attributes(attr):
    """Set the common attributes."""
    attr.set_attribute(
        attributes_helper.COMMON_ATTRIBUTES.get('AGENT'),
        AGENT)


def set_gae_attributes(attr):
    """Set the GAE environment common attributes."""
    for env_var, attribute_key in GAE_ATTRIBUTES.items():
        attribute_value = os.environ.get(env_var)
        attr.set_attribute(attribute_key, attribute_value)


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

    def emit(self, span_datas):
        """
        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param list of opencensus.trace.span_data.SpanData span_datas:
            SpanData tuples to emit
        """
        name = 'projects/{}'.format(self.project_id)

        stackdriver_spans = self.translate_to_stackdriver(span_datas)
        self.client.batch_write_spans(name, stackdriver_spans)

    def export(self, span_datas):
        """
        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param list of opencensus.trace.span_data.SpanData span_datas:
            SpanData tuples to export
        """
        self.transport.export(span_datas)

    def translate_to_stackdriver(self, span_datas):
        """Translate the spans json to Stackdriver format.

        See: https://cloud.google.com/trace/docs/reference/v2/rest/v2/
             projects.traces/batchWrite

        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param span_datas:
            SpanData tuples to emit

        :rtype: dict
        :returns: Spans in Google Cloud StackDriver Trace format.
        """

        top_span = span_datas[0]
        trace_id = top_span.context.trace_id if top_span.context is not None \
            else None

        spans_list = []

        for span in span_datas:
            span_name = 'projects/{}/traces/{}/spans/{}'.format(
                self.project_id, trace_id, span.span_id)

            attributes = Attributes(span.attributes)
            set_attributes(attributes)                

            span_json = {
                'name': span_name,
                'displayName': _get_truncatable_str(span.name),
                'startTime': span.start_time,
                'endTime': span.end_time,
                'spanId': str(span.span_id),
                'attributes': attributes.format_attributes_json(),
                'links': None,
                'status': span.status,
                'stackTrace': None,
                'timeEvents': None,
                'sameProcessAsParentSpan': span.same_process_as_parent_span,
                'childSpanCount': span.child_span_count
            }
            
            stack_trace = span.stack_trace
            if stack_trace is not None:
                span_json['stackTrace'] = stack_trace.format_stack_trace_json()
            
            if span.links is not None:
                span_json['links'] = {
                    'link': [
                        link.format_link_json() for link in span.links
                    ]
                }

            if span.time_events is not None:
                span_json['timeEvents'] =  {
                    'timeEvent': [
                        time_event.format_time_event_json()
                          for time_event in span.time_events]
                }

            if span.parent_span_id is not None:
                parent_span_id = str(span.parent_span_id)
                span_json['parentSpanId'] = parent_span_id

            spans_list.append(span_json)

        spans = {'spans': spans_list}
        return spans
