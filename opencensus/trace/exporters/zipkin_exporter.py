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

import datetime
import json
import logging
import requests
import calendar

from opencensus.trace.exporters import base
from opencensus.trace.exporters.transports import sync

DEFAULT_ENDPOINT = '/api/v2/spans'
DEFAULT_HOST_NAME = 'localhost'
DEFAULT_PORT = 9411
ZIPKIN_HEADERS = {'Content-Type': 'application/json'}

ISO_DATETIME_REGEX = '%Y-%m-%dT%H:%M:%S.%fZ'

SPAN_KIND_MAP = {
    0: None,  # span kind unspecified
    1: "SERVER",
    2: "CLIENT",
}

SUCCESS_STATUS_CODE = (200, 202)


class ZipkinExporter(base.Exporter):
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

    :type transport: :class:`type`
    :param transport: Class for creating new transport objects. It should
                      extend from the base :class:`.Transport` type and
                      implement :meth:`.Transport.export`. Defaults to
                      :class:`.SyncTransport`. The other option is
                      :class:`.BackgroundThreadTransport`.
    """

    def __init__(
            self,
            service_name='my_service',
            host_name=DEFAULT_HOST_NAME,
            port=DEFAULT_PORT,
            endpoint=DEFAULT_ENDPOINT,
            transport=sync.SyncTransport,
            ipv4=None,
            ipv6=None):
        self.service_name = service_name
        self.host_name = host_name
        self.port = port
        self.endpoint = endpoint
        self.url = self.get_url
        self.transport = transport(self)
        self.ipv4 = ipv4
        self.ipv6 = ipv6

    @property
    def get_url(self):
        return 'http://{}:{}{}'.format(
            self.host_name,
            self.port,
            self.endpoint)

    def emit(self, trace):
        """Send trace to Zipkin server, default using the v2 API.

        :type trace: dict
        :param trace: Trace data in dictionary format.
        """
        trace_id = trace.get('traceId')
        spans = trace.get('spans')

        try:
            zipkin_spans = self.translate_to_zipkin(trace_id, spans)
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

    def export(self, trace):
        self.transport.export(trace)

    def translate_to_zipkin(self, trace_id, spans):
        """Translate the opencensus spans to zipkin spans.

        :type trace_id: str
        :param trace_id: Trace ID.

        :type spans: list
        :param spans: List of spans to be exported.

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

        for span in spans:
            # Timestamp in zipkin spans is int of microseconds.
            start_datetime = datetime.datetime.strptime(
                span.get('startTime'),
                ISO_DATETIME_REGEX)
            start_timestamp_ms = calendar.timegm(
                start_datetime.timetuple()) * 1000 * 1000

            end_datetime = datetime.datetime.strptime(
                span.get('endTime'),
                ISO_DATETIME_REGEX)
            end_timestamp_ms = calendar.timegm(
                end_datetime.timetuple()) * 1000 * 1000

            duration_ms = end_timestamp_ms - start_timestamp_ms

            zipkin_span = {
                'traceId': trace_id,
                'id': str(span.get('spanId')),
                'name': span.get('displayName', {}).get('value'),
                'timestamp': int(round(start_timestamp_ms)),
                'duration': int(round(duration_ms)),
                'localEndpoint': local_endpoint,
                'tags': _extract_tags_from_span(span),
            }

            span_kind = span.get('kind')
            parent_span_id = span.get('parentSpanId')

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


def _extract_tags_from_span(span):
    tags = {}
    for attribute_key, attribute_value in span.get(
            'attributes', {}).get('attributeMap', {}).items():
        if not isinstance(attribute_value, dict):
            continue
        if attribute_value.get('string_value') is not None:
            value = attribute_value.get('string_value').get('value')
        elif attribute_value.get('int_value') is not None:
            value = str(attribute_value.get('int_value'))
        elif attribute_value.get('bool_value') is not None:
            value = str(attribute_value.get('bool_value'))
        else:
            logging.warn('Could not serialize tag {}'.format(attribute_key))
            continue
        tags[attribute_key] = value
    return tags
