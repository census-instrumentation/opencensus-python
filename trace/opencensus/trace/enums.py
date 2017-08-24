# Copyright 2017, OpenCensus Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Wrappers for protocol buffer enum types.

See
https://cloud.google.com/trace/docs/reference/v1/rpc/google.devtools.
cloudtrace.v1#google.devtools.cloudtrace.v1.ListTracesRequest.ViewType

https://cloud.google.com/trace/docs/reference/v1/rpc/google.devtools.
cloudtrace.v1#google.devtools.cloudtrace.v1.TraceSpan.SpanKind
"""


class Enum(object):
    class SpanKind(object):
        """
        Type of span. Can be used to specify additional relationships between
        spans in addition to a parent/child relationship.

        Attributes:
          SPAN_KIND_UNSPECIFIED (int): Unspecified.
          RPC_SERVER (int): Indicates that the span covers server-side handling
                            of an RPC or other remote network request.
          RPC_CLIENT (int): Indicates that the span covers the client-side
                            wrapper around an RPC or other remote request.
        """
        SPAN_KIND_UNSPECIFIED = 0
        RPC_SERVER = 1
        RPC_CLIENT = 2
