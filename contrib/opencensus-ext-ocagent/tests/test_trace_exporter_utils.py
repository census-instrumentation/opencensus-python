# Copyright 2018, OpenCensus Authors
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

import codecs
from datetime import datetime, timedelta
import unittest

from opencensus.common import utils as common_utils
from opencensus.ext.ocagent.trace_exporter import utils
from opencensus.ext.ocagent.trace_exporter.gen.opencensus.trace.v1 \
    import trace_pb2
from opencensus.trace import attributes as attributes_module
from opencensus.trace import link as link_module
from opencensus.trace import span as span_module
from opencensus.trace import span_context as span_context_module
from opencensus.trace import span_data as span_data_module
from opencensus.trace import status as status_module
from opencensus.trace import time_event as time_event_module
from opencensus.trace import tracestate as tracestate_module


class TestTraceExporterUtils(unittest.TestCase):
    def test_basic_span_translation(self):
        hex_encoder = codecs.getencoder('hex')

        span_data = span_data_module.SpanData(
            name="name",
            context=span_context_module.SpanContext(
                trace_id='6e0c63257de34c92bf9efcd03927272e'),
            span_id='6e0c63257de34c92',
            parent_span_id='6e0c63257de34c93',
            attributes={
                'test_str_key': 'test_str_value',
                'test_int_key': 1,
                'test_bool_key': False,
                'test_double_key': 567.89
            },
            start_time='2017-08-15T18:02:26.071158Z',
            end_time='2017-08-15T18:02:36.071158Z',
            child_span_count=None,
            stack_trace=None,
            time_events=None,
            links=None,
            status=None,
            same_process_as_parent_span=None,
            span_kind=0)

        pb_span = utils.translate_to_trace_proto(span_data)

        self.assertEqual(pb_span.name.value, "name")
        self.assertEqual(
            hex_encoder(pb_span.trace_id)[0],
            b'6e0c63257de34c92bf9efcd03927272e')
        self.assertEqual(hex_encoder(pb_span.span_id)[0], b'6e0c63257de34c92')
        self.assertEqual(
            hex_encoder(pb_span.parent_span_id)[0], b'6e0c63257de34c93')
        self.assertEqual(pb_span.kind, 0)

        self.assertEqual(len(pb_span.attributes.attribute_map), 4)
        self.assertEqual(
            pb_span.attributes.attribute_map['test_str_key'],
            trace_pb2.AttributeValue(
                string_value=trace_pb2.TruncatableString(
                    value='test_str_value')))

        self.assertEqual(pb_span.attributes.attribute_map['test_int_key'],
                         trace_pb2.AttributeValue(int_value=1))
        self.assertEqual(pb_span.attributes.attribute_map['test_bool_key'],
                         trace_pb2.AttributeValue(bool_value=False))
        self.assertEqual(pb_span.attributes.attribute_map['test_double_key'],
                         trace_pb2.AttributeValue(double_value=567.89))

        self.assertEqual(pb_span.start_time.ToJsonString(),
                         '2017-08-15T18:02:26.071158Z')
        self.assertEqual(pb_span.end_time.ToJsonString(),
                         '2017-08-15T18:02:36.071158Z')

        self.assertEqual(pb_span.child_span_count.value, 0)
        self.assertEqual(pb_span.same_process_as_parent_span.value, False)
        self.assertEqual(len(pb_span.time_events.time_event), 0)

        self.assertEqual(pb_span.status.code, 0)
        self.assertFalse(pb_span.status.message)

        self.assertEqual(len(pb_span.links.link), 0)
        self.assertEqual(len(pb_span.tracestate.entries), 0)

    def test_translate_none_span(self):
        pb_span = utils.translate_to_trace_proto(None)

        self.assertIsNone(pb_span)

    def test_translate_client_span_kind(self):
        client_span_data = span_data_module.SpanData(
            context=span_context_module.SpanContext(
                trace_id='6e0c63257de34c92bf9efcd03927272e'),
            span_id='6e0c63257de34c92',
            start_time='2017-08-15T18:02:26.071158Z',
            end_time='2017-08-15T18:02:36.071158Z',
            span_kind=span_module.SpanKind.CLIENT,
            same_process_as_parent_span=True,
            name=None,
            parent_span_id=None,
            attributes=None,
            child_span_count=None,
            stack_trace=None,
            time_events=None,
            links=None,
            status=None)

        pb_span = utils.translate_to_trace_proto(client_span_data)

        self.assertEqual(pb_span.kind, 2)
        self.assertEqual(pb_span.same_process_as_parent_span.value, True)

    def test_translate_server_span_kindt(self):
        server_span_data = span_data_module.SpanData(
            context=span_context_module.SpanContext(
                trace_id='6e0c63257de34c92bf9efcd03927272e'),
            span_id='6e0c63257de34c92',
            span_kind=span_module.SpanKind.SERVER,
            child_span_count=1,
            start_time=None,
            end_time=None,
            name=None,
            parent_span_id=None,
            attributes=None,
            same_process_as_parent_span=False,
            stack_trace=None,
            time_events=None,
            links=None,
            status=None)

        pb_span = utils.translate_to_trace_proto(server_span_data)

        self.assertEqual(pb_span.kind, 1)
        self.assertEqual(pb_span.child_span_count.value, 1)

    def test_translate_status(self):
        span_data = span_data_module.SpanData(
            context=span_context_module.SpanContext(
                trace_id='6e0c63257de34c92bf9efcd03927272e'),
            span_id='6e0c63257de34c92',
            status=status_module.Status(
                code=2, message='ERR', details='details'),
            span_kind=span_module.SpanKind.SERVER,
            start_time=None,
            end_time=None,
            child_span_count=None,
            name=None,
            parent_span_id=None,
            attributes=None,
            same_process_as_parent_span=False,
            stack_trace=None,
            time_events=None,
            links=None)

        pb_span = utils.translate_to_trace_proto(span_data)

        self.assertEqual(pb_span.status.code, 2)
        self.assertEqual(pb_span.status.message, 'ERR')

    def test_translate_links(self):
        hex_encoder = codecs.getencoder('hex')

        span_data = span_data_module.SpanData(
            context=span_context_module.SpanContext(
                trace_id='6e0c63257de34c92bf9efcd03927272e'),
            span_id='6e0c63257de34c92',
            links=[
                link_module.Link(
                    trace_id='0e0c63257de34c92bf9efcd03927272e',
                    span_id='0e0c63257de34c92',
                    type=link_module.Type.TYPE_UNSPECIFIED,
                    attributes=attributes_module.Attributes(
                        attributes={
                            'test_str_key': 'test_str_value',
                            'test_int_key': 1,
                            'test_bool_key': False,
                            'test_double_key': 567.89
                        })),
                link_module.Link(
                    trace_id='1e0c63257de34c92bf9efcd03927272e',
                    span_id='1e0c63257de34c92',
                    type=link_module.Type.CHILD_LINKED_SPAN),
                link_module.Link(
                    trace_id='2e0c63257de34c92bf9efcd03927272e',
                    span_id='2e0c63257de34c92',
                    type=link_module.Type.PARENT_LINKED_SPAN)
            ],
            span_kind=span_module.SpanKind.SERVER,
            status=None,
            start_time=None,
            end_time=None,
            child_span_count=None,
            name=None,
            parent_span_id=None,
            attributes=None,
            same_process_as_parent_span=False,
            stack_trace=None,
            time_events=None)

        pb_span = utils.translate_to_trace_proto(span_data)

        self.assertEqual(len(pb_span.links.link), 3)
        self.assertEqual(
            hex_encoder(pb_span.links.link[0].trace_id)[0],
            b'0e0c63257de34c92bf9efcd03927272e')
        self.assertEqual(
            hex_encoder(pb_span.links.link[1].trace_id)[0],
            b'1e0c63257de34c92bf9efcd03927272e')
        self.assertEqual(
            hex_encoder(pb_span.links.link[2].trace_id)[0],
            b'2e0c63257de34c92bf9efcd03927272e')

        self.assertEqual(
            hex_encoder(pb_span.links.link[0].span_id)[0], b'0e0c63257de34c92')
        self.assertEqual(
            hex_encoder(pb_span.links.link[1].span_id)[0], b'1e0c63257de34c92')
        self.assertEqual(
            hex_encoder(pb_span.links.link[2].span_id)[0], b'2e0c63257de34c92')

        self.assertEqual(pb_span.links.link[0].type, 0)
        self.assertEqual(pb_span.links.link[1].type, 1)
        self.assertEqual(pb_span.links.link[2].type, 2)

        self.assertEqual(
            len(pb_span.links.link[0].attributes.attribute_map), 4)
        self.assertEqual(
            len(pb_span.links.link[1].attributes.attribute_map), 0)
        self.assertEqual(
            len(pb_span.links.link[2].attributes.attribute_map), 0)

        self.assertEqual(
            pb_span.links.link[0].attributes.attribute_map['test_str_key'],
            trace_pb2.AttributeValue(
                string_value=trace_pb2.TruncatableString(
                    value='test_str_value')))

        self.assertEqual(
            pb_span.links.link[0].attributes.attribute_map['test_int_key'],
            trace_pb2.AttributeValue(int_value=1))
        self.assertEqual(
            pb_span.links.link[0].attributes.attribute_map['test_bool_key'],
            trace_pb2.AttributeValue(bool_value=False))
        self.assertEqual(
            pb_span.links.link[0].attributes.attribute_map['test_double_key'],
            trace_pb2.AttributeValue(double_value=567.89))

    def test_translate_time_events(self):

        annotation0_ts = datetime.utcnow() + timedelta(seconds=-10)
        annotation1_ts = datetime.utcnow() + timedelta(seconds=-9)
        message0_ts = datetime.utcnow() + timedelta(seconds=-8)
        message1_ts = datetime.utcnow() + timedelta(seconds=-7)
        message2_ts = datetime.utcnow() + timedelta(seconds=-6)

        span_data = span_data_module.SpanData(
            context=span_context_module.SpanContext(
                trace_id='6e0c63257de34c92bf9efcd03927272e'),
            span_id='6e0c63257de34c92',
            time_events=[
                time_event_module.TimeEvent(
                    timestamp=annotation0_ts,
                    annotation=time_event_module.Annotation(
                        description="hi there0",
                        attributes=attributes_module.Attributes(
                            attributes={
                                'test_str_key': 'test_str_value',
                                'test_int_key': 1,
                                'test_bool_key': False,
                                'test_double_key': 567.89
                            }))),
                time_event_module.TimeEvent(
                    timestamp=annotation1_ts,
                    annotation=time_event_module.Annotation(
                        description="hi there1")),
                time_event_module.TimeEvent(
                    timestamp=message0_ts,
                    message_event=time_event_module.MessageEvent(
                        id=0,
                        type=time_event_module.Type.SENT,
                        uncompressed_size_bytes=10,
                        compressed_size_bytes=1)),
                time_event_module.TimeEvent(
                    timestamp=message1_ts,
                    message_event=time_event_module.MessageEvent(
                        id=1,
                        type=time_event_module.Type.RECEIVED,
                        uncompressed_size_bytes=20,
                        compressed_size_bytes=2)),
                time_event_module.TimeEvent(
                    timestamp=message2_ts,
                    message_event=time_event_module.MessageEvent(
                        id=2,
                        type=time_event_module.Type.TYPE_UNSPECIFIED,
                        uncompressed_size_bytes=30,
                        compressed_size_bytes=3))
            ],
            span_kind=span_module.SpanKind.SERVER,
            status=None,
            start_time=None,
            end_time=None,
            child_span_count=None,
            name=None,
            parent_span_id=None,
            attributes=None,
            same_process_as_parent_span=False,
            stack_trace=None,
            links=None)

        pb_span = utils.translate_to_trace_proto(span_data)

        self.assertEqual(len(pb_span.time_events.time_event), 5)

        event0 = pb_span.time_events.time_event[0]
        event1 = pb_span.time_events.time_event[1]
        event2 = pb_span.time_events.time_event[2]
        event3 = pb_span.time_events.time_event[3]
        event4 = pb_span.time_events.time_event[4]
        self.assertEqual(event0.time.ToDatetime(), annotation0_ts)
        self.assertEqual(event1.time.ToDatetime(), annotation1_ts)
        self.assertEqual(event2.time.ToDatetime(), message0_ts)
        self.assertEqual(event3.time.ToDatetime(), message1_ts)
        self.assertEqual(event4.time.ToDatetime(), message2_ts)

        self.assertEqual(event0.annotation.description.value, "hi there0")
        self.assertEqual(event1.annotation.description.value, "hi there1")

        self.assertEqual(len(event0.annotation.attributes.attribute_map), 4)
        self.assertEqual(len(event1.annotation.attributes.attribute_map), 0)

        self.assertEqual(
            event0.annotation.attributes.attribute_map['test_str_key'],
            trace_pb2.AttributeValue(
                string_value=trace_pb2.TruncatableString(
                    value='test_str_value')))

        self.assertEqual(
            event0.annotation.attributes.attribute_map['test_int_key'],
            trace_pb2.AttributeValue(int_value=1))
        self.assertEqual(
            event0.annotation.attributes.attribute_map['test_bool_key'],
            trace_pb2.AttributeValue(bool_value=False))
        self.assertEqual(
            event0.annotation.attributes.attribute_map['test_double_key'],
            trace_pb2.AttributeValue(double_value=567.89))

        self.assertEqual(event2.message_event.id, 0)
        self.assertEqual(event3.message_event.id, 1)
        self.assertEqual(event4.message_event.id, 2)

        self.assertEqual(event2.message_event.uncompressed_size, 10)
        self.assertEqual(event3.message_event.uncompressed_size, 20)
        self.assertEqual(event4.message_event.uncompressed_size, 30)

        self.assertEqual(event2.message_event.compressed_size, 1)
        self.assertEqual(event3.message_event.compressed_size, 2)
        self.assertEqual(event4.message_event.compressed_size, 3)

        self.assertEqual(event2.message_event.type, 1)
        self.assertEqual(event3.message_event.type, 2)
        self.assertEqual(event4.message_event.type, 0)

    def test_translate_time_events_invalid(self):

        ts = datetime.utcnow() + timedelta(seconds=-10)

        span_data = span_data_module.SpanData(
            context=span_context_module.SpanContext(
                trace_id='6e0c63257de34c92bf9efcd03927272e'),
            span_id='6e0c63257de34c92',
            time_events=[time_event_module.TimeEvent(timestamp=ts)],
            span_kind=span_module.SpanKind.SERVER,
            status=None,
            start_time=None,
            end_time=None,
            child_span_count=None,
            name=None,
            parent_span_id=None,
            attributes=None,
            same_process_as_parent_span=False,
            stack_trace=None,
            links=None)

        pb_span = utils.translate_to_trace_proto(span_data)

        self.assertEqual(len(pb_span.time_events.time_event), 0)

    def test_translate_tracestate(self):

        tracestate = tracestate_module.Tracestate()
        tracestate.append("k1", "v1")
        tracestate.append("k2", "v2")
        tracestate.append("k3", "v3")

        client_span_data = span_data_module.SpanData(
            context=span_context_module.SpanContext(
                trace_id='6e0c63257de34c92bf9efcd03927272e',
                tracestate=tracestate),
            span_id='6e0c63257de34c92',
            start_time='2017-08-15T18:02:26.071158Z',
            end_time='2017-08-15T18:02:36.071158Z',
            span_kind=span_module.SpanKind.CLIENT,
            same_process_as_parent_span=True,
            name=None,
            parent_span_id=None,
            attributes=None,
            child_span_count=None,
            stack_trace=None,
            time_events=None,
            links=None,
            status=None)

        pb_span = utils.translate_to_trace_proto(client_span_data)

        self.assertEqual(len(pb_span.tracestate.entries), 3)
        self.assertEqual(pb_span.tracestate.entries[0].key, "k1")
        self.assertEqual(pb_span.tracestate.entries[0].value, "v1")
        self.assertEqual(pb_span.tracestate.entries[1].key, "k2")
        self.assertEqual(pb_span.tracestate.entries[1].value, "v2")
        self.assertEqual(pb_span.tracestate.entries[2].key, "k3")
        self.assertEqual(pb_span.tracestate.entries[2].value, "v3")

    def test_add_attribute_value(self):
        pb_span = trace_pb2.Span()

        utils.add_proto_attribute_value(pb_span.attributes, 'int_key', 42)
        utils.add_proto_attribute_value(pb_span.attributes, 'bool_key', True)
        utils.add_proto_attribute_value(pb_span.attributes, 'string_key',
                                        'value')
        utils.add_proto_attribute_value(pb_span.attributes, 'unicode_key',
                                        u'uvalue')
        utils.add_proto_attribute_value(pb_span.attributes, 'dict_key',
                                        {"a": "b"})

        self.assertEqual(len(pb_span.attributes.attribute_map), 5)
        self.assertEqual(pb_span.attributes.attribute_map['int_key'].int_value,
                         42)
        self.assertEqual(
            pb_span.attributes.attribute_map['bool_key'].bool_value, True)
        self.assertEqual(
            pb_span.attributes.attribute_map['string_key'].string_value.value,
            'value')
        self.assertEqual(
            pb_span.attributes.attribute_map['unicode_key'].string_value.value,
            'uvalue')
        self.assertEqual(
            pb_span.attributes.attribute_map['dict_key'].string_value.value,
            "{'a': 'b'}")

    def test_set_proto_event(self):
        pb_span = trace_pb2.Span()
        pb_event = pb_span.time_events.time_event.add()

        message_event = time_event_module.MessageEvent(
            id=0,
            type=time_event_module.Type.SENT,
            uncompressed_size_bytes=10,
            compressed_size_bytes=1)

        utils.set_proto_message_event(pb_event.message_event, message_event)

        self.assertEqual(pb_event.message_event.id, 0)
        self.assertEqual(pb_event.message_event.type, 1)
        self.assertEqual(pb_event.message_event.uncompressed_size, 10)
        self.assertEqual(pb_event.message_event.compressed_size, 1)

    def test_set_annotation_with_attributes(self):
        pb_span = trace_pb2.Span()
        pb_event = pb_span.time_events.time_event.add()

        annotation = time_event_module.Annotation(
            description="hi there",
            attributes=attributes_module.Attributes(
                attributes={
                    'test_str_key': 'test_str_value',
                    'test_int_key': 1,
                    'test_bool_key': False,
                    'test_double_key': 567.89
                }))

        utils.set_proto_annotation(pb_event.annotation, annotation)

        self.assertEqual(pb_event.annotation.description.value, "hi there")
        self.assertEqual(len(pb_event.annotation.attributes.attribute_map), 4)
        self.assertEqual(
            pb_event.annotation.attributes.attribute_map['test_str_key'],
            trace_pb2.AttributeValue(
                string_value=trace_pb2.TruncatableString(
                    value='test_str_value')))
        self.assertEqual(
            pb_event.annotation.attributes.attribute_map['test_int_key'],
            trace_pb2.AttributeValue(int_value=1))
        self.assertEqual(
            pb_event.annotation.attributes.attribute_map['test_bool_key'],
            trace_pb2.AttributeValue(bool_value=False))
        self.assertEqual(
            pb_event.annotation.attributes.attribute_map['test_double_key'],
            trace_pb2.AttributeValue(double_value=567.89))

    def test_set_annotation_without_attributes(self):
        pb_span = trace_pb2.Span()
        pb_event0 = pb_span.time_events.time_event.add()
        pb_event1 = pb_span.time_events.time_event.add()

        annotation0 = time_event_module.Annotation(description="hi there0")
        annotation1 = time_event_module.Annotation(
            description="hi there1", attributes=attributes_module.Attributes())

        utils.set_proto_annotation(pb_event0.annotation, annotation0)
        utils.set_proto_annotation(pb_event1.annotation, annotation1)

        self.assertEqual(pb_event0.annotation.description.value, "hi there0")
        self.assertEqual(pb_event1.annotation.description.value, "hi there1")
        self.assertEqual(len(pb_event0.annotation.attributes.attribute_map), 0)
        self.assertEqual(len(pb_event1.annotation.attributes.attribute_map), 0)

    def test_datetime_str_to_proto_ts_conversion(self):
        now = datetime.utcnow()
        delta = now - datetime(1970, 1, 1)
        expected_seconds = int(delta.total_seconds())
        expected_nanos = delta.microseconds * 1000

        proto_ts = utils.proto_ts_from_datetime_str(
            common_utils.to_iso_str(now))
        self.assertEqual(proto_ts.seconds, int(expected_seconds))
        self.assertEqual(proto_ts.nanos, expected_nanos)

    def test_datetime_str_to_proto_ts_conversion_none(self):
        proto_ts = utils.proto_ts_from_datetime_str(None)
        self.assertEquals(proto_ts.seconds, 0)
        self.assertEquals(proto_ts.nanos, 0)

    def test_datetime_str_to_proto_ts_conversion_empty(self):
        proto_ts = utils.proto_ts_from_datetime_str('')
        self.assertEquals(proto_ts.seconds, 0)
        self.assertEquals(proto_ts.nanos, 0)

    def test_datetime_str_to_proto_ts_conversion_invalid(self):
        proto_ts = utils.proto_ts_from_datetime_str('2018 08 22 T 11:53')
        self.assertEquals(proto_ts.seconds, 0)
        self.assertEquals(proto_ts.nanos, 0)

    def test_hex_str_to_proto_bytes_conversion(self):
        hex_encoder = codecs.getencoder('hex')

        proto_bytes = utils.hex_str_to_bytes_str(
            '00010203040506070a0b0c0d0eff')
        self.assertEqual(
            hex_encoder(proto_bytes)[0], b'00010203040506070a0b0c0d0eff')

    def test_datetime_to_proto_ts_conversion_none(self):
        proto_ts = utils.proto_ts_from_datetime(None)
        self.assertEquals(proto_ts.seconds, 0)
        self.assertEquals(proto_ts.nanos, 0)

    def test_datetime_to_proto_ts_conversion(self):
        now = datetime.utcnow()
        delta = now - datetime(1970, 1, 1)
        expected_seconds = int(delta.total_seconds())
        expected_nanos = delta.microseconds * 1000

        proto_ts = utils.proto_ts_from_datetime(now)
        self.assertEqual(proto_ts.seconds, int(expected_seconds))
        self.assertEqual(proto_ts.nanos, expected_nanos)

    def test_datetime_to_proto_ts_conversion_zero(self):
        zero = datetime(1970, 1, 1)

        proto_ts = utils.proto_ts_from_datetime(zero)
        self.assertEqual(proto_ts.seconds, 0)
        self.assertEqual(proto_ts.nanos, 0)
