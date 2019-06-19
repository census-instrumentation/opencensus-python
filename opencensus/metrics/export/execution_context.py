# Copyright 2019, OpenCensus Authors
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

_measurements_slot = RuntimeContext.register_slot(
    'measurements',
    lambda: {})


def get_measurements_map():
    return RuntimeContext.measurements


def set_measurements_map(measurements):
    RuntimeContext.measurements = measurements


def clear():
    """Clear the context, used in test."""
    _measurements_slot.clear()
