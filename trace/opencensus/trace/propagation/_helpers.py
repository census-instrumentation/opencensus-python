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

_ENABLED_BITMASK = 1


def _get_enabled_trace_option(trace_options):
    """Get the last bit from the trace options which is the enabled field.

    :type trace_options: str
    :param trace_options: 1 byte field which indicates 8 trace options,
                          currently only have the enabled option. 1 means
                          enabled, 0 means not enabled.

    :rtype: bool
    :returns: Enabled tracing or not.
    """
    enabled = bool(int(trace_options) & _ENABLED_BITMASK)

    return enabled
