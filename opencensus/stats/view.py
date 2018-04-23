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

from opencensus.stats.measure import BaseMeasure
from opencensus.stats.aggregation import DistributionAggregation
from opencensus.tags.tag import Tag
from opencensus.tags import tag_key

class View(object):
    def __init__(self, name, description, columns, measure, aggregation):
        self._name = name
        self._description = description

        column_list = []
        for tag_key in columns:
            column_list.append(tag_key)

        self._columns = column_list

        self._measure = measure
        self._aggregation = aggregation

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def columns(self):
        return self._columns

    @property
    def measure(self):
        return self._measure

    @property
    def aggregation(self):
        return self._aggregation
