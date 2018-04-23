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
        self._view = view
        self._start = start
        self._end = end
        self._rows = rows if rows is not None else {}

    @property
    def view(self):
        return self._view

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @property
    def rows(self):
        return self._rows
