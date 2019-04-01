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

"""Export the spans data to Zipkin Collector."""

import json
import logging

import requests

from opencensus.common.transports import sync
from opencensus.common.utils import check_str_length
from opencensus.common.utils import timestamp_to_microseconds
from opencensus.trace import base_exporter

DEFAULT_ENDPOINT = '/api/v2/spans'
DEFAULT_HOST_NAME = 'localhost'
DEFAULT_PORT = 9411
DEFAULT_PROTOCOL = 'http'
ZIPKIN_HEADERS = {'Content-Type': 'application/json'}

SPAN_KIND_MAP = {
    0: None,  # span kind unspecified
    1: "SERVER",
    2: "CLIENT",
}

SUCCESS_STATUS_CODE = (200, 202)


class ZipkinExporter(base_exporter.Exporter):
    """Export the spans to Zipkin.

    See: http://zipkin.io/zipkin-api/#

    :type service_name: str
    :param service_name: Service that logged an annotation in a trace.
                         Classifier when query for spans.

    :type host_name: str
    :param host_name: (Optional) The host name of the Zipkin server.

    :type port: int
    :param port: (Optional) The port of the Zipkin server.

    :type end_point: str
    :param end_point: (Optional) The path for the span exporting endpoint.

    :type protocol: str
    :param protocol: (Optional) The protocol used for the request.

    :type transport: :class:`type`
    :param transport: Class for creating new transport objects. It should
                      extend from the base_exporter :class:`.Transport` type
                      and implement :meth:`.Transport.export`. Defaults to
                      :class:`.SyncTransport`. The other option is
                      :class:`.AsyncTransport`.
    """

    def __init__(
            self,
            service_name='my_service',
            host_name=DEFAULT_HOST_NAME,
            port=DEFAULT_PORT,
            endpoint=DEFAULT_ENDPOINT,
            protocol=DEFAULT_PROTOCOL,
            transport=sync.SyncTransport,
            ipv4=None,
            ipv6=None):
        self.service_name = service_name
        self.host_name = host_name
        self.port = port
        self.endpoint = endpoint
        self.protocol = protocol
        self.url = self.get_url
        self.transport = transport(self)
        self.ipv4 = ipv4
        self.ipv6 = ipv6

    @property
    def get_url(self):
        return '{}://{}:{}{}'.format(
            self.protocol,
            self.host_name,
            self.port,
            self.endpoint)

    def emit(self, span_datas):
        """Send SpanData tuples to Zipkin server, default using the v2 API.

        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param list of opencensus.trace.span_data.SpanData span_datas:
            SpanData tuples to emit
        """

        try:
            zipkin_spans = self.translate_to_zipkin(span_datas)
            result = requests.post(
                url=self.url,
                data=json.dumps(zipkin_spans),
                headers=ZIPKIN_HEADERS)

            if result.status_code not in SUCCESS_STATUS_CODE:
                logging.error(
                    "Failed to send spans to Zipkin server! Spans are {}"
                    .format(zipkin_spans))
        except Exception as e:  # pragma: NO COVER
            logging.error(getattr(e, 'message', e))

    def export(self, span_datas):
        self.transport.export(span_datas)

    def translate_to_zipkin(self, span_datas):
        """Translate the opencensus spans to zipkin spans.

        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param span_datas:
            SpanData tuples to emit

        :rtype: list
        :returns: List of zipkin format spans.
        """

        local_endpoint = {
            'serviceName': self.service_name,
            'port': self.port,
        }

        if self.ipv4 is not None:
            local_endpoint['ipv4'] = self.ipv4

        if self.ipv6 is not None:
            local_endpoint['ipv6'] = self.ipv6

        zipkin_spans = []

        for span in span_datas:
            # Timestamp in zipkin spans is int of microseconds.
            start_timestamp_mus = timestamp_to_microseconds(span.start_time)
            end_timestamp_mus = timestamp_to_microseconds(span.end_time)
            duration_mus = end_timestamp_mus - start_timestamp_mus

            zipkin_span = {
                'traceId': span.context.trace_id,
                'id': str(span.span_id),
                'name': span.name,
                'timestamp': int(round(start_timestamp_mus)),
                'duration': int(round(duration_mus)),
                'localEndpoint': local_endpoint,
                'tags': _extract_tags_from_span(span.attributes),
                'annotations': _extract_annotations_from_span(span),
            }

            span_kind = span.span_kind
            parent_span_id = span.parent_span_id

            if span_kind is not None:
                kind = SPAN_KIND_MAP.get(span_kind)
                # Zipkin API for span kind only accept
                # enum(CLIENT|SERVER|PRODUCER|CONSUMER|Absent)
                if kind is not None:
                    zipkin_span['kind'] = kind

            if parent_span_id is not None:
                zipkin_span['parentId'] = str(parent_span_id)

            zipkin_spans.append(zipkin_span)

        return zipkin_spans


def _extract_tags_from_span(attr):
    if attr is None:
        return {}
    tags = {}
    for attribute_key, attribute_value in attr.items():
        if isinstance(attribute_value, (int, bool, float)):
            value = str(attribute_value)
        elif isinstance(attribute_value, str):
            res, _ = check_str_length(str_to_check=attribute_value)
            value = res
        else:
            logging.warn('Could not serialize tag {}'.format(attribute_key))
            continue
        tags[attribute_key] = value
    return tags


def _extract_annotations_from_span(span):
    """Extract and convert time event annotations to zipkin annotations"""
    if span.time_events is None:
        return []

    annotations = []
    for time_event in span.time_events:
        annotation = time_event.annotation
        if not annotation:
            continue

        event_timestamp_mus = timestamp_to_microseconds(time_event.timestamp)
        annotations.append({'timestamp': int(round(event_timestamp_mus)),
                            'value': annotation.description})

    return annotations
