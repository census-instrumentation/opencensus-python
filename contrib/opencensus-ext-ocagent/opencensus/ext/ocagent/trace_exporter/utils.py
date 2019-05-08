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

"""Translates opencensus span data to trace proto"""

from google.protobuf.wrappers_pb2 import BoolValue, UInt32Value
from opencensus.ext.ocagent import utils as ocagent_utils
from opencensus.proto.trace.v1 import trace_pb2


def translate_to_trace_proto(span_data):
    """Translates the opencensus spans to ocagent proto spans.

    :type span_data: :class:`~opencensus.trace.span_data.SpanData`
    :param span_data: SpanData tuples to convert to protobuf spans

    :rtype: :class:`~opencensus.proto.trace.Span`
    :returns: Protobuf format span.
    """

    if not span_data:
        return None

    pb_span = trace_pb2.Span(
        name=trace_pb2.TruncatableString(value=span_data.name),
        kind=span_data.span_kind,
        trace_id=hex_str_to_bytes_str(span_data.context.trace_id),
        span_id=hex_str_to_bytes_str(span_data.span_id),
        parent_span_id=hex_str_to_bytes_str(span_data.parent_span_id)
        if span_data.parent_span_id is not None else None,
        start_time=ocagent_utils.proto_ts_from_datetime_str(
            span_data.start_time),
        end_time=ocagent_utils.proto_ts_from_datetime_str(span_data.end_time),
        status=trace_pb2.Status(
            code=span_data.status.code,
            message=span_data.status.message)
        if span_data.status is not None else None,
        same_process_as_parent_span=BoolValue(
            value=span_data.same_process_as_parent_span)
        if span_data.same_process_as_parent_span is not None
        else None,
        child_span_count=UInt32Value(value=span_data.child_span_count)
        if span_data.child_span_count is not None else None)

    # attributes
    if span_data.attributes is not None:
        for attribute_key, attribute_value \
                in span_data.attributes.items():
            add_proto_attribute_value(
                pb_span.attributes,
                attribute_key,
                attribute_value)

    # time events
    if span_data.time_events is not None:
        for span_data_event in span_data.time_events:
            if span_data_event.message_event is not None:
                pb_event = pb_span.time_events.time_event.add()
                pb_event.time.FromJsonString(span_data_event.timestamp)
                set_proto_message_event(
                    pb_event.message_event,
                    span_data_event.message_event)
            elif span_data_event.annotation is not None:
                pb_event = pb_span.time_events.time_event.add()
                pb_event.time.FromJsonString(span_data_event.timestamp)
                set_proto_annotation(
                    pb_event.annotation,
                    span_data_event.annotation)

    # links
    if span_data.links is not None:
        for link in span_data.links:
            pb_link = pb_span.links.link.add(
                trace_id=hex_str_to_bytes_str(link.trace_id),
                span_id=hex_str_to_bytes_str(link.span_id),
                type=link.type)

            if link.attributes is not None and \
                    link.attributes.attributes is not None:
                for attribute_key, attribute_value \
                        in link.attributes.attributes.items():
                    add_proto_attribute_value(
                        pb_link.attributes,
                        attribute_key,
                        attribute_value)

    # tracestate
    if span_data.context.tracestate is not None:
        for (key, value) in span_data.context.tracestate.items():
            pb_span.tracestate.entries.add(key=key, value=value)

    return pb_span


def set_proto_message_event(
        pb_message_event,
        span_data_message_event):
    """Sets properties on the protobuf message event.

    :type pb_message_event:
        :class: `~opencensus.proto.trace.Span.TimeEvent.MessageEvent`
    :param pb_message_event: protobuf message event

    :type span_data_message_event:
        :class: `~opencensus.trace.time_event.MessageEvent`
    :param span_data_message_event: opencensus message event
    """

    pb_message_event.type = span_data_message_event.type
    pb_message_event.id = span_data_message_event.id
    pb_message_event.uncompressed_size = \
        span_data_message_event.uncompressed_size_bytes
    pb_message_event.compressed_size = \
        span_data_message_event.compressed_size_bytes


def set_proto_annotation(pb_annotation, span_data_annotation):
    """Sets properties on the protobuf Span annotation.

    :type pb_annotation:
        :class: `~opencensus.proto.trace.Span.TimeEvent.Annotation`
    :param pb_annotation: protobuf annotation

    :type span_data_annotation:
        :class: `~opencensus.trace.time_event.Annotation`
    :param span_data_annotation: opencensus annotation

    """

    pb_annotation.description.value = span_data_annotation.description
    if span_data_annotation.attributes is not None \
            and span_data_annotation.attributes.attributes is not None:
        for attribute_key, attribute_value in \
                span_data_annotation.attributes.attributes.items():
            add_proto_attribute_value(
                pb_annotation.attributes,
                attribute_key,
                attribute_value)


def hex_str_to_bytes_str(hex_str):
    """Converts the hex string to bytes string.

    :type hex_str: str
    :param hex_str: The hex tring representing trace_id or span_id.

    :rtype: str
    :returns: string representing byte array
    """

    return bytes(bytearray.fromhex(hex_str))


def add_proto_attribute_value(
        pb_attributes,
        attribute_key,
        attribute_value):
    """Sets string, int, boolean or float value on protobuf
        span, link or annotation attributes.

    :type pb_attributes:
        :class: `~opencensus.proto.trace.Span.Attributes`
    :param pb_attributes: protobuf Span's attributes property

    :type attribute_key: str
    :param attribute_key: attribute key to set

    :type attribute_value: str or int or bool or float
    :param attribute_value: attribute value
    """

    if isinstance(attribute_value, bool):
        pb_attributes.attribute_map[attribute_key].\
            bool_value = attribute_value
    elif isinstance(attribute_value, int):
        pb_attributes.attribute_map[attribute_key].\
            int_value = attribute_value
    elif isinstance(attribute_value, str):
        pb_attributes.attribute_map[attribute_key].\
            string_value.value = attribute_value
    elif isinstance(attribute_value, float):
        pb_attributes.attribute_map[attribute_key].\
            double_value = attribute_value
    else:
        pb_attributes.attribute_map[attribute_key].\
            string_value.value = str(attribute_value)
