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
from opencensus.tags import tag_map
from datetime import datetime


class ViewData(object):
    def __init__(self, view, start_time, end_time, rows=None):
        self._view = view
        self._start_time = start_time
        self._end_time = end_time
        self._rows = rows if rows is not None else {}
        self._tag_value_aggregation_map = {}
        self._tag_map = {}

    @property
    def view(self):
        return self._view

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    @property
    def rows(self):
        return self._rows

    @property
    def tag_value_aggregation_map(self):
        return self._tag_value_aggregation_map

    def start(self):
        self._start_time = datetime.utcnow().isoformat() + 'Z'

    def end(self):
        self._end_time = datetime.utcnow().isoformat() + 'Z'

    def get_tag_map(self, context):
        if context.items() <= self._tag_map.items():
            return self._tag_map
        else:
            tags = self._tag_map
            for tag_key, tag_value in context.items():
                tags[tag_key] = tag_value
            return tags

    def get_tag_values(self, tags, columns):
        tag_values = []
        i = 0
        while i < len(columns):
            tag_key = columns[i]
            if tag_key in tags:
                tag_values.append(tags.get(tag_key))
            i += 1
        return tag_values

    def record(self, context, value, timestamp):
        tag_values = self.get_tag_values(tags=self.get_tag_map(context), columns=self._view.columns)
        for tag_value in tag_values:
            if tag_value not in self._tag_value_aggregation_map:
                self._tag_value_aggregation_map[tag_value] = self._view.aggregation
            self._tag_value_aggregation_map[tag_value] = value
