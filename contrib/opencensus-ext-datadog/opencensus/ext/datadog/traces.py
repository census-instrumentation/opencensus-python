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
from collections import defaultdict
from datetime import datetime

import bitarray

from opencensus.common.transports import sync
from opencensus.common.utils import ISO_DATETIME_REGEX
from opencensus.ext.datadog.transport import DDTransport
from opencensus.trace import base_exporter
from opencensus.trace import span_data


class Options(object):
    """ Options contains options for configuring the exporter.
    The address can be empty as the prometheus client will
    assume it's localhost

    :type namespace: str
    :param namespace: Namespace specifies the namespaces to which metric keys
    are appended. Defaults to ''.

    :type service: str
    :param service: service specifies the service name used for tracing.

    :type trace_addr: str
    :param trace_addr: trace_addr specifies the host[:port] address of the
    Datadog Trace Agent. It defaults to localhost:8126

    :type global_tags: dict
    :param global_tags: global_tags is a set of tags that will be
    applied to all exported spans.
    """
    def __init__(self, service='', trace_addr='localhost:8126',
                 global_tags={}):
        self._service = service
        self._trace_addr = trace_addr
        for k, v in global_tags.items():
            if not isinstance(k, str) or not isinstance(v, str):
                raise TypeError(
                    "global tags must be dictionary of string string")
        self._global_tags = global_tags

    @property
    def trace_addr(self):
        """ specifies the host[:port] address of the Datadog Trace Agent.
        """
        return self._trace_addr

    @property
    def service(self):
        """ Specifies the service name used for tracing.
        """
        return self._service

    @property
    def global_tags(self):
        """ Specifies the namespaces to which metric keys are appended
        """
        return self._global_tags


class DatadogTraceExporter(base_exporter.Exporter):
    """ A exporter that send traces and trace spans to Datadog.

    :type options: :class:`~opencensus.ext.datadog.Options`
    :param options: An options object with the parameters to instantiate the
                         Datadog Exporter.

    :type transport:
        :class:`opencensus.common.transports.sync.SyncTransport` or
        :class:`opencensus.common.transports.async_.AsyncTransport`
    :param transport: An instance of a Transport to send data with.
    """
    def __init__(self, options, transport=sync.SyncTransport):
        self._options = options
        self._transport = transport(self)
        self._dd_transport = DDTransport(options.trace_addr)

    @property
    def transport(self):
        """ The transport way to be sent data to server
        (default is sync).
        """
        return self._transport

    @property
    def options(self):
        """ Options to be used to configure the exporter
        """
        return self._options

    def export(self, span_datas):
        """
        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param list of opencensus.trace.span_data.SpanData span_datas:
            SpanData tuples to export
        """
        if span_datas is not None:  # pragma: NO COVER
            self.transport.export(span_datas)

    def emit(self, span_datas):
        """
        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param list of opencensus.trace.span_data.SpanData span_datas:
            SpanData tuples to emit
        """
        # Map each span data to it's corresponding trace id
        trace_span_map = defaultdict(list)
        for sd in span_datas:
            trace_span_map[sd.context.trace_id] += [sd]

        dd_spans = []
        # Write spans to Datadog
        for _, sds in trace_span_map.items():
            # convert to the legacy trace json for easier refactoring
            trace = span_data.format_legacy_trace_json(sds)
            dd_spans.append(self.translate_to_datadog(trace))

        self._dd_transport.send_traces(dd_spans)

    def translate_to_datadog(self, trace):
        """Translate the spans json to Datadog format.

        :type trace: dict
        :param trace: Trace dictionary

        :rtype: dict
        :returns: Spans in Datadog Trace format.
        """

        spans_json = trace.get('spans')
        trace_id = convert_id(trace.get('traceId')[8:])
        dd_trace = []
        for span in spans_json:
            span_id_int = convert_id(span.get('spanId'))
            # Set meta at the end.
            meta = self.options.global_tags.copy()

            dd_span = {
                'span_id': span_id_int,
                'trace_id': trace_id,
                'name': "opencensus",
                'service': self.options.service,
                'resource': span.get("displayName").get("value"),
            }

            start_time = datetime.strptime(span.get('startTime'),
                                           ISO_DATETIME_REGEX)

            # The start time of the request in nanoseconds from the unix epoch.
            epoch = datetime.utcfromtimestamp(0)
            dd_span["start"] = int((start_time - epoch).total_seconds() *
                                   1000.0 * 1000.0 * 1000.0)

            end_time = datetime.strptime(span.get('endTime'),
                                         ISO_DATETIME_REGEX)
            duration_td = end_time - start_time

            # The duration of the request in nanoseconds.
            dd_span["duration"] = int(duration_td.total_seconds() * 1000.0 *
                                      1000.0 * 1000.0)

            if span.get('parentSpanId') is not None:
                parent_span_id = convert_id(span.get('parentSpanId'))
                dd_span['parent_id'] = parent_span_id

            code = STATUS_CODES.get(span["status"].get("code"))
            if code is None:
                code = {}
                code["message"] = "ERR_CODE_" + str(span["status"].get("code"))
                code["status"] = 500

            # opencensus.trace.span.SpanKind
            dd_span['type'] = to_dd_type(span.get("kind"))
            dd_span["error"] = 0
            if 4 <= code.get("status") // 100 <= 5:
                dd_span["error"] = 1
                meta["error.type"] = code.get("message")

                if span.get("status").get("message") is not None:
                    meta["error.msg"] = span.get("status").get("message")

            meta["opencensus.status_code"] = str(code.get("status"))
            meta["opencensus.status"] = code.get("message")

            if span.get("status").get("message") is not None:
                meta["opencensus.status_description"] = span.get("status").get(
                    "message")

            atts = span.get("attributes").get("attributeMap")
            atts_to_metadata(atts, meta=meta)

            dd_span["meta"] = meta
            dd_trace.append(dd_span)

        return dd_trace


def atts_to_metadata(atts, meta={}):
    """Translate the attributes to Datadog meta format.

    :type atts: dict
    :param atts: Attributes dictionary

    :rtype: dict
    :returns: meta dictionary
    """
    for key, elem in atts.items():
        value = value_from_atts_elem(elem)
        if value != "":
            meta[key] = value

    return meta


def value_from_atts_elem(elem):
    """ value_from_atts_elem takes an attribute element and retuns a string value

    :type elem: dict
    :param elem: Element from the attributes map

    :rtype: str
    :return: A string rep of the element value
    """
    if elem.get('string_value') is not None:
        return elem.get('string_value').get('value')
    elif elem.get('int_value') is not None:
        return str(elem.get('int_value'))
    elif elem.get('bool_value') is not None:
        return str(elem.get('bool_value'))
    elif elem.get('double_value') is not None:
        return str(elem.get('double_value').get('value'))
    return ""


def to_dd_type(oc_kind):
    """ to_dd_type takes an OC kind int ID and returns a dd string of the span type

    :type oc_kind: int
    :param oc_kind: OC kind id

    :rtype: string
    :returns: A string of the Span type.
    """
    if oc_kind == 2:
        return "client"
    elif oc_kind == 1:
        return "server"
    else:
        return "unspecified"


def new_trace_exporter(option):
    """ new_trace_exporter returns an exporter
    that exports traces to Datadog.
    """
    if option.service == "":
        raise ValueError("Service can not be empty string.")

    exporter = DatadogTraceExporter(options=option)
    return exporter


def convert_id(str_id):
    """ convert_id takes a string and converts that to an int that is no
    more than 64 bits wide. It does this by first converting the string
    to a bit array then taking up to the 64th bit and creating and int.
    This is equivlent to the go-exporter ID converter
    ` binary.BigEndian.Uint64(s.SpanContext.SpanID[:])`

    :type str_id: str
    :param str_id: string id

    :rtype: int
    :returns: An int that is no more than 64 bits wide
    """
    id_bitarray = bitarray.bitarray(endian='big')
    id_bitarray.frombytes(str_id.encode())
    cut_off = len(id_bitarray)
    if cut_off > 64:
        cut_off = 64
    id_cutoff_bytearray = id_bitarray[:cut_off].tobytes()
    id_int = int(codecs.encode(id_cutoff_bytearray, 'hex'), 16)
    return id_int


# https://opencensus.io/tracing/span/status/
STATUS_CODES = {
    0: {
        "message": "OK",
        "status": 200
    },
    1: {
        "message": "CANCELLED",
        "status": 499
    },
    2: {
        "message": "UNKNOWN",
        "status": 500
    },
    3: {
        "message": "INVALID_ARGUMENT",
        "status": 400
    },
    4: {
        "message": "DEADLINE_EXCEEDED",
        "status": 504
    },
    5: {
        "message": "NOT_FOUND",
        "status": 404
    },
    6: {
        "message": "ALREADY_EXISTS",
        "status": 409
    },
    7: {
        "message": "PERMISSION_DENIED",
        "status": 403
    },
    8: {
        "message": "RESOURCE_EXHAUSTED",
        "status": 429
    },
    9: {
        "message": "FAILED_PRECONDITION",
        "status": 400
    },
    10: {
        "message": "ABORTED",
        "status": 409
    },
    11: {
        "message": "OUT_OF_RANGE",
        "status": 400
    },
    12: {
        "message": "UNIMPLEMENTED",
        "status": 502
    },
    13: {
        "message": "INTERNAL",
        "status": 500
    },
    14: {
        "message": "UNAVAILABLE",
        "status": 503
    },
    15: {
        "message": "DATA_LOSS",
        "status": 501
    },
    16: {
        "message": "UNAUTHENTICATED",
        "status": 401
    },
}
