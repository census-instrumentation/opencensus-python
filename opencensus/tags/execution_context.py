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

from opencensus.common.runtime_context import RuntimeContext

_current_tag_map_slot = RuntimeContext.register_slot('current_tag_map', None)


def get_current_tag_map():
    return RuntimeContext.current_tag_map


def set_current_tag_map(current_tag_map):
    RuntimeContext.current_tag_map = current_tag_map


def clear():
    """Clear the context, used in test."""
    _current_tag_map_slot.clear()
