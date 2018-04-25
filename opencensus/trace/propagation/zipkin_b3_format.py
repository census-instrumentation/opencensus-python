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


from opencensus.trace.propagation.text_format import TextFormatPropagator

_TRACE_PREFIX = 'x-b3'
_TRACE_ID_KEY = '{}-traceid'.format(_TRACE_PREFIX)
_SPAN_ID_KEY = '{}-spanid'.format(_TRACE_PREFIX)
_TRACE_OPTIONS_KEY = '{}-sampled'.format(_TRACE_PREFIX)

DEFAULT_TRACE_OPTIONS = '1'


class ZipkinB3FormatPropagator(TextFormatPropagator):
    """"This class provides the basic utilities for extracting the trace
    information from a carrier which is a dict to form a SpanContext. And
    generating a dict using the provided SpanContext.

    The trace prefix is set to match the B3 headers.
    """
    _TRACE_ID_KEY = _TRACE_ID_KEY
    _SPAN_ID_KEY = _SPAN_ID_KEY
    _TRACE_OPTIONS_KEY = _TRACE_OPTIONS_KEY
    DEFAULT_TRACE_OPTIONS = DEFAULT_TRACE_OPTIONS

    HEADERS = [_TRACE_ID_KEY, _SPAN_ID_KEY, _TRACE_OPTIONS_KEY]
