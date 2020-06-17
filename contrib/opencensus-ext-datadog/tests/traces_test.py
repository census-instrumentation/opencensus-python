import unittest

import mock

from opencensus.ext.datadog.traces import (DatadogTraceExporter, Options,
                                           atts_to_metadata, convert_id,
                                           new_trace_exporter, to_dd_type,
                                           value_from_atts_elem)
from opencensus.trace import span_context
from opencensus.trace import span_data as span_data_module


class TestTraces(unittest.TestCase):
    def setUp(self):
        pass

    def test_convert_id(self):
        test_cases = [{
            'input': 'd17b83f89a2cbb08c2fa4469',
            'expected': 0x6431376238336638,
        }, {
            'input': '1ff346aeb5d12443',
            'expected': 0x3166663334366165,
        }, {
            'input': '8c9b71d2ffb05ede97bea00a',
            'expected': 0x3863396237316432,
        }, {
            'input': 'a3e1b9b4ce7d2e33',
            'expected': 0x6133653162396234,
        }, {
            'input': '2f79a1a078c0a4d070094440',
            'expected': 0x3266373961316130,
        }, {
            'input': '0018b3f50e44f875',
            'expected': 0x3030313862336635,
        }, {
            'input': 'cba7b2832de221dbc1ac8e77',
            'expected': 0x6362613762323833,
        }, {
            'input': 'a3e1b9b4',
            'expected': 0x6133653162396234,
        }]
        for tc in test_cases:
            self.assertEqual(convert_id(tc['input']), tc['expected'])

    def test_to_dd_type(self):
        self.assertEqual(to_dd_type(1), "server")
        self.assertEqual(to_dd_type(2), "client")
        self.assertEqual(to_dd_type(3), "unspecified")

    def test_value_from_atts_elem(self):
        test_cases = [{
            'elem': {
                'string_value': {
                    'value': 'StringValue'
                }
            },
            'expected': 'StringValue'
        }, {
            'elem': {
                'int_value': 10
            },
            'expected': '10'
        }, {
            'elem': {
                'bool_value': True
            },
            'expected': 'True'
        }, {
            'elem': {
                'bool_value': False
            },
            'expected': 'False'
        }, {
            'elem': {
                'double_value': {
                    'value': 2.1
                }
            },
            'expected': '2.1'
        }, {
            'elem': {
                'somthing_les': 2.1
            },
            'expected': ''
        }]

        for tc in test_cases:
            self.assertEqual(value_from_atts_elem(tc['elem']), tc['expected'])

    def test_export(self):
        mock_dd_transport = mock.Mock()
        exporter = DatadogTraceExporter(options=Options(),
                                        transport=MockTransport)
        exporter._dd_transport = mock_dd_transport
        exporter.export({})
        self.assertTrue(exporter.transport.export_called)

    @mock.patch('opencensus.ext.datadog.traces.'
                'DatadogTraceExporter.translate_to_datadog',
                return_value=None)
    def test_emit(self, mr_mock):

        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        span_datas = [
            span_data_module.SpanData(
                name='span',
                context=span_context.SpanContext(trace_id=trace_id),
                span_id=None,
                parent_span_id=None,
                attributes=None,
                start_time=None,
                end_time=None,
                child_span_count=None,
                stack_trace=None,
                annotations=None,
                message_events=None,
                links=None,
                status=None,
                same_process_as_parent_span=None,
                span_kind=0,
            )
        ]

        mock_dd_transport = mock.Mock()
        exporter = DatadogTraceExporter(
            options=Options(service="dd-unit-test"),
            transport=MockTransport)
        exporter._dd_transport = mock_dd_transport

        exporter.emit(span_datas)
        # mock_dd_transport.send_traces.assert_called_with(datadog_spans)
        self.assertTrue(mock_dd_transport.send_traces.called)

    def test_translate_to_datadog(self):
        test_cases = [
            {
                'status': {'code': 0},
                'prt_span_id': '6e0c63257de34c92',
                'expt_prt_span_id': 0x3665306336333235,
                'attributes': {
                    'attributeMap': {
                        'key': {
                            'string_value': {
                                'truncated_byte_count': 0,
                                'value': 'value'
                            }
                        },
                        'key_double': {
                            'double_value': {
                                'value': 123.45
                            }
                        },
                        'http.host': {
                            'string_value': {
                                'truncated_byte_count': 0,
                                'value': 'host'
                            }
                        }
                    }
                },
                'meta': {
                    'key': 'value',
                    'key_double': '123.45',
                    'http.host': 'host',
                    'opencensus.status': 'OK',
                    'opencensus.status_code': '200'
                },
                'error': 0
            },
            {
                'status': {'code': 23},
                'attributes': {
                    'attributeMap': {}
                },
                'meta': {
                    'error.type': 'ERR_CODE_23',
                    'opencensus.status': 'ERR_CODE_23',
                    'opencensus.status_code': '500'
                },
                'error': 1
            },
            {
                'status': {'code': 23, 'message': 'I_AM_A_TEAPOT'},
                'attributes': {
                    'attributeMap': {}
                },
                'meta': {
                    'error.type': 'ERR_CODE_23',
                    'opencensus.status': 'ERR_CODE_23',
                    'opencensus.status_code': '500',
                    'opencensus.status_description': 'I_AM_A_TEAPOT',
                    'error.msg': 'I_AM_A_TEAPOT'
                },
                'error': 1
            },
            {
                'status': {'code': 0, 'message': 'OK'},
                'attributes': {
                    'attributeMap': {}
                },
                'meta': {
                    'opencensus.status': 'OK',
                    'opencensus.status_code': '200',
                    'opencensus.status_description': 'OK'
                },
                'error': 0
            }
        ]
        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        expected_trace_id = 0x3764653334633932
        span_id = '6e0c63257de34c92'
        expected_span_id = 0x3665306336333235
        span_name = 'test span'
        start_time = '2019-09-19T14:05:15.000000Z'
        start_time_epoch = 1568901915000000000
        end_time = '2019-09-19T14:05:16.000000Z'
        span_duration = 1 * 1000 * 1000 * 1000

        for tc in test_cases:
            mock_dd_transport = mock.Mock()
            opts = Options(service="dd-unit-test")
            tran = MockTransport
            exporter = DatadogTraceExporter(options=opts, transport=tran)
            exporter._dd_transport = mock_dd_transport
            trace = {
                'spans': [{
                    'displayName': {
                        'value': span_name,
                        'truncated_byte_count': 0
                    },
                    'spanId': span_id,
                    'startTime': start_time,
                    'endTime': end_time,
                    'parentSpanId': tc.get('prt_span_id'),
                    'attributes': tc.get('attributes'),
                    'someRandomKey': 'this should not be included in result',
                    'childSpanCount': 0,
                    'kind': 1,
                    'status': tc.get('status')
                }],
                'traceId':
                trace_id,
            }

            spans = list(exporter.translate_to_datadog(trace))
            expected_traces = [{
                'span_id': expected_span_id,
                'trace_id': expected_trace_id,
                'name': 'opencensus',
                'service': 'dd-unit-test',
                'resource': span_name,
                'start': start_time_epoch,
                'duration': span_duration,
                'meta': tc.get('meta'),
                'type': 'server',
                'error': tc.get('error')
            }]

            if tc.get('prt_span_id') is not None:
                expected_traces[0]['parent_id'] = tc.get('expt_prt_span_id')
            self.assertEqual.__self__.maxDiff = None
            self.assertEqual(spans, expected_traces)

    def test_atts_to_metadata(self):
        test_cases = [
            {
                'input': {
                    'key_string': {
                        'string_value': {
                            'truncated_byte_count': 0,
                            'value': 'value'
                        }
                    },
                    'key_double': {
                        'double_value': {
                            'value': 123.45
                        }
                    },
                },
                'input_meta': {},
                'output': {
                    'key_string': 'value',
                    'key_double': '123.45'
                }
            },
            {
                'input': {
                    'key_string': {
                        'string_value': {
                            'truncated_byte_count': 0,
                            'value': 'value'
                        }
                    },
                },
                'input_meta': {
                    'key': 'in_meta'
                },
                'output': {
                    'key_string': 'value',
                    'key': 'in_meta'
                }
            },
            {
                'input': {
                    'key_string': {
                        'string_value': {
                            'truncated_byte_count': 0,
                            'value': 'value'
                        }
                    },
                    'invalid': {
                        'unknown_value': "na"
                    }
                },
                'input_meta': {},
                'output': {
                    'key_string': 'value',
                }
            }
        ]

        for tc in test_cases:
            out = atts_to_metadata(tc.get('input'), meta=tc.get('input_meta'))
            self.assertEqual(out, tc.get('output'))

    def test_new_trace_exporter(self):
        self.assertRaises(ValueError, new_trace_exporter, Options())
        try:
            new_trace_exporter(Options(service="test"))
        except ValueError:
            self.fail("new_trace_exporter raised ValueError unexpectedly")

    def test_constructure(self):
        self.assertRaises(TypeError, Options, global_tags={'int_bad': 1})
        try:
            Options(global_tags={'good': 'tag'})
        except TypeError:
            self.fail("Constructure raised TypeError unexpectedly")


class MockTransport(object):
    def __init__(self, exporter=None):
        self.export_called = False
        self.exporter = exporter

    def export(self, trace):
        self.export_called = True


if __name__ == '__main__':
    unittest.main()
