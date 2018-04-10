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

from opencensus.stats import aggregation
from opencensus.stats import aggregation_data
from opencensus.stats import measure
from opencensus.stats import view
from opencensus.tags import tag_value
import time

class ViewData(object):
    def __init__(self, view, start, end, rows=None):
        self.view = view.view
        self.start = start
        self.end = end
        self.rows = dict({tag_value : aggregation_data} or {})
