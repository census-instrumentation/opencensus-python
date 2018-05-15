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

from datetime import datetime


class ViewData(object):
    """View Data is the aggregated data for a particular view

    :type view:
    :param view: The view associated with this view data

    :type start_time: datetime
    :param start_time: the start time for this view data

    :type end_time: datetime
    :param end_time: the end time for this view data

    """
    def __init__(self,
                 view,
                 start_time,
                 end_time):
        self._view = view
        self._start_time = start_time
        self._end_time = end_time
        self._tag_value_aggregation_map = {}
        self._tag_map = {}

    @property
    def view(self):
        """the current view in the view data"""
        return self._view

    @property
    def start_time(self):
        """the current start time in the view data"""
        return self._start_time

    @property
    def end_time(self):
        """the current end time in the view data"""
        return self._end_time

    @property
    def tag_value_aggregation_map(self):
        """the current tag value aggregation map in the view data"""
        return self._tag_value_aggregation_map

    @property
    def tag_map(self):
        return self._tag_map

    def start(self):
        """sets the start time for the view data"""
        self._start_time = datetime.utcnow().isoformat() + 'Z'

    def end(self):
        """sets the end time for the view data"""
        self._end_time = datetime.utcnow().isoformat() + 'Z'

    def get_tag_map(self, context):
        """function to return the tag map based on the context"""
        if context.items() <= self.tag_map.items():
            return self.tag_map
        else:
            tags = self.tag_map
            for tag_key, tag_value in context.items():
                tags[tag_key] = tag_value
            return tags

    def get_tag_values(self, tags, columns):
        """function to get the tag values from tags and columns"""
        tag_values = []
        i = 0
        while i < len(columns):
            tag_key = columns[i]
            if tag_key in tags:
                tag_values.append(tags.get(tag_key))
            else:
                tag_values.append(None)
            i += 1
        return tag_values

    def record(self, context, value, timestamp):
        """records the view data against context"""
        tag_values = self.get_tag_values(tags=self.get_tag_map(context),
                                         columns=self.view.columns)
        tuple_vals = tuple(tag_values)
        for val in tuple_vals:
            if val not in self.tag_value_aggregation_map:
                self.tag_value_aggregation_map[val] = self.view.aggregation
            self.tag_value_aggregation_map.get(val).add(value)
