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
from opencensus.trace import span_data as span_data_module
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
            span_data_module.SpanData(
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
                    'displayName': {
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
        project_id = 'PROJECT'
        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        span_name = 'test span'
        span_id = '6e0c63257de34c92'
        attributes = {
            'attributeMap': {
                'key': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'value'
                    }
                },
                'http.host': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'host'
                    }
                }
            }
        }
        parent_span_id = '6e0c63257de34c93'
        start_time = 'test start time'
        end_time = 'test end time'
        trace = {
            'spans': [
                {
                    'displayName': {
                        'value': span_name,
                        'truncated_byte_count': 0
                    },
                    'spanId': span_id,
                    'startTime': start_time,
                    'endTime': end_time,
                    'parentSpanId': parent_span_id,
                    'attributes': attributes,
                    'someRandomKey': 'this should not be included in result',
                    'childSpanCount': 0
                }
            ],
            'traceId': trace_id
        }

        client = mock.Mock()
        client.project = project_id
        exporter = stackdriver_exporter.StackdriverExporter(
            client=client,
            project_id=project_id)

        spans = exporter.translate_to_stackdriver(trace)

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
                            },
                            '/http/host': {
                                'string_value': {
                                    'truncated_byte_count': 0,
                                    'value': 'host'
                                }
                            }
                        }
                    },
                    'spanId': str(span_id),
                    'startTime': start_time,
                    'endTime': end_time,
                    'parentSpanId': str(parent_span_id),
                    'status': None,
                    'links': None,
                    'stackTrace': None,
                    'timeEvents': None,
                    'childSpanCount': 0,
                    'sameProcessAsParentSpan': None
                }
            ]
        }

        self.assertEqual(spans, expected_traces)

    def test_translate_common_attributes_to_stackdriver_no_attribute_map(self):
        project_id = 'PROJECT'
        client = mock.Mock()
        client.project = project_id
        exporter = stackdriver_exporter.StackdriverExporter(
            client=client,
            project_id=project_id)

        attributes = {'outer key': 'some value'}
        expected_attributes = {'outer key': 'some value'}

        exporter.map_attributes(attributes)
        self.assertEqual(attributes, expected_attributes)

    def test_translate_common_attributes_to_stackdriver_none(self):
        project_id = 'PROJECT'
        client = mock.Mock()
        client.project = project_id
        exporter = stackdriver_exporter.StackdriverExporter(
            client=client,
            project_id=project_id)

        # does not throw
        exporter.map_attributes(None)

    def test_translate_common_attributes_to_stackdriver(self):
        project_id = 'PROJECT'
        client = mock.Mock()
        client.project = project_id
        exporter = stackdriver_exporter.StackdriverExporter(
            client=client,
            project_id=project_id)

        attributes = {
            'outer key': 'some value',
            'attributeMap': {
                'key': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'value'
                    }
                },
                'component': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'http'
                    }
                },
                'error.message': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'error message'
                    }
                },
                'error.name': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'error name'
                    }
                },
                'http.host': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'host'
                    }
                },
                'http.method': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'GET'
                    }
                },
                'http.status_code': {
                    'int_value': {
                        'value': 200
                    }
                },
                'http.url': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'http://host:port/path?query'
                    }
                },
                'http.user_agent': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'some user agent'
                    }
                },
                'http.client_city': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'Redmond'
                    }
                },
                'http.client_country': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'USA'
                    }
                },
                'http.client_protocol': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'HTTP 1.1'
                    }
                },
                'http.client_region': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'WA'
                    }
                },
                'http.request_size': {
                    'int_value': {
                        'value': 100
                    }
                },
                'http.response_size': {
                    'int_value': {
                        'value': 10
                    }
                },
                'pid': {
                    'int_value': {
                        'value': 123456789
                    }
                },
                'tid': {
                    'int_value': {
                        'value': 987654321
                    }
                },
                'stacktrace': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'at unknown'
                    }
                },
                'grpc.host_port': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'localhost:50051'
                    }
                },
                'grpc.method': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'post'
                    }
                }
            }
        }

        expected_attributes = {
            'outer key': 'some value',
            'attributeMap': {
                'key': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'value'
                    }
                },
                '/component': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'http'
                    }
                },
                '/error/message': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'error message'
                    }
                },
                '/error/name': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'error name'
                    }
                },
                '/http/host': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'host'
                    }
                },
                '/http/method': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'GET'
                    }
                },
                '/http/status_code': {
                    'int_value': {
                        'value': 200
                    }
                },
                '/http/url': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'http://host:port/path?query'
                    }
                },
                '/http/user_agent': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'some user agent'
                    }
                },
                '/http/client_city': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'Redmond'
                    }
                },
                '/http/client_country': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'USA'
                    }
                },
                '/http/client_protocol': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'HTTP 1.1'
                    }
                },
                '/http/client_region': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'WA'
                    }
                },
                '/http/request/size': {
                    'int_value': {
                        'value': 100
                    }
                },
                '/http/response/size': {
                    'int_value': {
                        'value': 10
                    }
                },
                '/pid': {
                    'int_value': {
                        'value': 123456789
                    }
                },
                '/tid': {
                    'int_value': {
                        'value': 987654321
                    }
                },
                '/stacktrace': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'at unknown'
                    }
                },
                '/grpc/host_port': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'localhost:50051'
                    }
                },
                '/grpc/method': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'post'
                    }
                }
            }
        }

        exporter.map_attributes(attributes)
        self.assertEqual(attributes, expected_attributes)


class Test_set_attributes_gae(unittest.TestCase):

    def test_set_attributes_gae(self):
        import os

        trace = {'spans': [
            {
                'attributes': {}
            }
        ]}

        expected = {
            'attributes': {
                'attributeMap': {
                    'g.co/gae/app/module': {
                        'string_value': {
                            'truncated_byte_count': 0,
                            'value': 'service'
                        }
                    },
                    'g.co/gae/app/instance': {
                        'string_value': {
                            'truncated_byte_count': 0,
                            'value': 'flex'
                        }
                    },
                    'g.co/gae/app/version': {
                        'string_value': {
                            'truncated_byte_count': 0,
                            'value': 'version'
                        }
                    },
                    'g.co/gae/app/project': {
                        'string_value': {
                            'truncated_byte_count': 0,
                            'value': 'project'
                        }
                    },
                    'g.co/agent': {
                        'string_value': {
                            'truncated_byte_count': 0,
                            'value': 'opencensus-python [{}]'.format(
                                stackdriver_exporter.VERSION
                            )
                        }
                    },
                }
            }
        }

        with mock.patch.dict(
                os.environ,
                {stackdriver_exporter._APPENGINE_FLEXIBLE_ENV_VM: 'vm',
                 stackdriver_exporter._APPENGINE_FLEXIBLE_ENV_FLEX: 'flex',
                 'GOOGLE_CLOUD_PROJECT': 'project',
                 'GAE_SERVICE': 'service',
                 'GAE_VERSION': 'version'}):
            self.assertTrue(stackdriver_exporter.is_gae_environment())
            stackdriver_exporter.set_attributes(trace)

        span = trace.get('spans')[0]
        self.assertEqual(span, expected)


class MockTransport(object):
    def __init__(self, exporter=None):
        self.export_called = False
        self.exporter = exporter

    def export(self, trace):
        self.export_called = True
