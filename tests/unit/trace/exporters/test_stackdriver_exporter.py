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

import unittest

import mock

from opencensus.trace import span_context
from opencensus.trace import attributes as attributes_module
from opencensus.trace import link, span_data, stack_trace, time_event
from opencensus.trace.exporters import stackdriver_exporter


class _Client(object):
    def __init__(self, project=None):
        if project is None:
            project = 'PROJECT'

        self.project = project


class TestStackdriverExporter(unittest.TestCase):

    def test_constructor_default(self):
        patch = mock.patch(
            'opencensus.trace.exporters.stackdriver_exporter.Client',
            new=_Client)

        with patch:
            exporter = stackdriver_exporter.StackdriverExporter()

        project_id = 'PROJECT'
        self.assertEqual(exporter.project_id, project_id)

    def test_constructor_explicit(self):
        client = mock.Mock()
        project_id = 'PROJECT'
        client.project = project_id
        transport = mock.Mock()

        exporter = stackdriver_exporter.StackdriverExporter(
            client=client,
            project_id=project_id,
            transport=transport)

        self.assertIs(exporter.client, client)
        self.assertEqual(exporter.project_id, project_id)

    def test_export(self):
        client = mock.Mock()
        project_id = 'PROJECT'
        client.project = project_id
        exporter = stackdriver_exporter.StackdriverExporter(
            client=client,
            project_id=project_id,
            transport=MockTransport)
        exporter.export({})

        self.assertTrue(exporter.transport.export_called)

    def test_emit(self):
        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        span_datas = [
            span_data.SpanData(
                name='span',
                context=span_context.SpanContext(trace_id=trace_id),
                span_id='1111',
                parent_span_id=None,
                attributes=None,
                start_time=None,
                end_time=None,
                child_span_count=None,
                stack_trace=None,
                time_events=None,
                links=None,
                status=None,
                same_process_as_parent_span=None,
                span_kind=0,
            )
        ]

        stackdriver_spans = {
            'spans': [
                {
                    'status': None,
                    'childSpanCount': None,
                    'links': None,
                    'startTime': None,
                    'spanId': '1111',
                    'attributes': {
                        'attributeMap': {
                            'g.co/agent': {
                                'string_value': {
                                    'truncated_byte_count': 0,
                                    'value': 'opencensus-python [{}]'.format(
                                        stackdriver_exporter.VERSION
                                    )
                                }
                            }
                        }
                    },
                    'stackTrace': None,
                    'displayName':
                        {
                            'truncated_byte_count': 0,
                            'value': 'span'
                        },
                    'name': 'projects/PROJECT/traces/{}/spans/1111'.format(
                        trace_id
                    ),
                    'timeEvents': None,
                    'endTime': None,
                    'sameProcessAsParentSpan': None
                }
            ]
        }

        client = mock.Mock()
        project_id = 'PROJECT'
        client.project = project_id

        exporter = stackdriver_exporter.StackdriverExporter(
            client=client,
            project_id=project_id)

        exporter.emit(span_datas)

        name = 'projects/{}'.format(project_id)

        client.batch_write_spans.assert_called_with(name, stackdriver_spans)
        self.assertTrue(client.batch_write_spans.called)

    def test_translate_to_stackdriver(self):
        self.maxDiff = None
        project_id = 'PROJECT'
        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        span_name = 'test span'
        span_id = '6e0c63257de34c92'
        attributes = {'key': 'value'}

        parent_span_id = '6e0c63257de34c93'
        start_time = 'test start time'
        end_time = 'test end time'

        import datetime
        s = '2017-08-15T18:02:26.071158'
        time = datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%f')

        time_events = [
            time_event.TimeEvent(
                timestamp=time)
        ]

        links = [
            link.Link(
                trace_id=trace_id,
                span_id=span_id,
                type=link.Type.CHILD_LINKED_SPAN)
        ]
        
        strace = stack_trace.StackTrace(
            stack_trace_hash_id=1)
        
        span_datas = [
            span_data.SpanData(
                name=span_name,
                context=span_context.SpanContext(trace_id=trace_id),
                span_id=span_id,
                parent_span_id=parent_span_id,
                attributes=attributes,
                start_time=start_time,
                end_time=end_time,
                child_span_count=0,
                stack_trace=strace,
                time_events=time_events,
                links=links,
                status=None,
                same_process_as_parent_span=None,
                span_kind=0
            )
        ]

        client = mock.Mock()
        client.project = project_id
        exporter = stackdriver_exporter.StackdriverExporter(
            client=client,
            project_id=project_id)

        spans = exporter.translate_to_stackdriver(span_datas)

        expected_traces = {
            'spans': [
                {
                    'name': 'projects/{}/traces/{}/spans/{}'.format(
                        project_id, trace_id, span_id),
                    'displayName': {
                        'value': span_name,
                        'truncated_byte_count': 0
                    },
                    'attributes': {
                        'attributeMap': {
                            'g.co/agent': {
                                'string_value': {
                                    'truncated_byte_count': 0,
                                    'value': 'opencensus-python [{}]'.format(
                                        stackdriver_exporter.VERSION
                                    )
                                }
                            },
                            'key': {
                                'string_value': {
                                    'truncated_byte_count': 0,
                                    'value': 'value'
                                }
                            }
                        }
                    },
                    'spanId': str(span_id),
                    'startTime': start_time,
                    'endTime': end_time,
                    'parentSpanId': str(parent_span_id),
                    'status': None,
                    'links': {
                        'link': [{
                                'trace_id': trace_id,
                                'span_id': span_id,
                                'type': link.Type.CHILD_LINKED_SPAN
                            }
                        ]
                    },
                    'stackTrace': {'stack_trace_hash_id': 1},
                    'timeEvents': {
                        'timeEvent': [{
                            'time': time.isoformat() + 'Z'
                        }]
                    },
                    'childSpanCount': 0,
                    'sameProcessAsParentSpan': None
                }
            ]
        }
        self.assertEqual(spans, expected_traces)


class Test_set_attributes_gae(unittest.TestCase):

    def test_set_attributes_gae(self):
        import os

        attributes = attributes_module.Attributes()
        attribute_map = {
            'g.co/gae/app/service': 'service',
            'g.co/gae/app/version': 'version',
            'g.co/gae/app/project': 'project',
            'g.co/agent': 'opencensus-python [{}]'.format(
                stackdriver_exporter.VERSION)
        }

        expected = attributes_module.Attributes(attribute_map)
        with mock.patch.dict(
                os.environ,
                {stackdriver_exporter._APPENGINE_FLEXIBLE_ENV_VM: 'vm',
                 stackdriver_exporter._APPENGINE_FLEXIBLE_ENV_FLEX: 'flex',
                 'GAE_FLEX_PROJECT': 'project',
                 'GAE_FLEX_SERVICE': 'service',
                 'GAE_FLEX_VERSION': 'version'}):
            self.assertTrue(stackdriver_exporter.is_gae_environment())
            stackdriver_exporter.set_attributes(attributes)

        self.assertEqual(
            attributes.format_attributes_json(), 
            expected.format_attributes_json())


class MockTransport(object):
    def __init__(self, exporter=None):
        self.export_called = False
        self.exporter = exporter

    def export(self, trace):
        self.export_called = True
