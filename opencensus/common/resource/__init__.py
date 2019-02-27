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

from opencensus.common.resource.resource import Resource
from opencensus.common.resource.resource import check_ascii_256
from opencensus.common.resource.resource import get_from_env
from opencensus.common.resource.resource import logger
from opencensus.common.resource.resource import parse_labels


__all__ = [
    'Resource',
    'check_ascii_256',
    'get_from_env',
    'logger',
    'parse_labels',
]
