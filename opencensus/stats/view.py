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


class View(object):
    """A view defines a specific aggregation and a set of tag keys

    :type name: str
    :param name: name of the view

    :type description: str
    :param description: description of the view

    :type columns: (:class: '~opencensus.tags.tag_key.TagKey')
    :param columns: the columns that the tag keys will aggregate on for this
                    view

    :type measure: :class: '~opencensus.stats.measure.Measure'
    :param measure: the measure to be aggregated by the view

    :type aggregation: :class: '~opencensus.stats.aggregation.BaseAggregation'
    :param aggregation: the aggregation the view will support

    """
    def __init__(self, name, description, columns, measure, aggregation):
        self._name = name
        self._description = description
        self._columns = columns
        self._measure = measure
        self._aggregation = aggregation

    @property
    def name(self):
        """the name of the current view"""
        return self._name

    @property
    def description(self):
        """the description of the current view"""
        return self._description

    @property
    def columns(self):
        """the columns of the current view"""
        return self._columns

    @property
    def measure(self):
        """the measure of the current view"""
        return self._measure

    @property
    def aggregation(self):
        """the aggregation of the current view"""
        return self._aggregation
