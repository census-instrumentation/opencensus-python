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
from opencensus.tags import execution_context


class MeasurementMap(object):
    """Measurement Map is a map from Measures to measured values
    to be recorded at the same time

    :type measure_to_view_map: :class: '~opencensus.stats.measure_to_view_map.
                                        MeasureToViewMap'
    :param measure_to_view_map: the measure to view map that will store the
                                recorded stats with tags

    :type: attachments: dict
    :param attachments: the contextual information about the attachment value.

    """
    def __init__(self, measure_to_view_map, attachments=None):
        self._measurement_map = {}
        self._measure_to_view_map = measure_to_view_map
        self._attachments = attachments

    @property
    def measurement_map(self):
        """the current measurement map"""
        return self._measurement_map

    @property
    def measure_to_view_map(self):
        """the current measure to view map for the measurement map"""
        return self._measure_to_view_map

    @property
    def attachments(self):
        """the current contextual information about the attachment value."""
        return self._attachments

    def measure_int_put(self, measure, value):
        """associates the measure of type Int with the given value"""
        self._measurement_map[measure] = value

    def measure_float_put(self, measure, value):
        """associates the measure of type Float with the given value"""
        self._measurement_map[measure] = value

    def measure_put_attachment(self, key, value):
        """Associate the contextual information of an Exemplar to this MeasureMap
            Contextual information is represented as key - value string pairs.
            If this method is called multiple times with the same key,
            only the last value will be kept.
        """
        if self._attachments is None:
            self._attachments = dict()

        if key is None or not isinstance(key, str):
            raise TypeError('attachment key should not be '
                            'empty and should be a string')
        if value is None or not isinstance(value, str):
            raise TypeError('attachment value should not be '
                            'empty and should be a string')

        self._attachments[key] = value

    def record(self, tag_map_tags=execution_context.get_current_tag_map()):
        """records all the measures at the same time with a tag_map.
        tag_map could either be explicitly passed to the method, or implicitly
        read from current execution context.
        """
        self.measure_to_view_map.record(
                tags=tag_map_tags,
                measurement_map=self.measurement_map,
                timestamp=datetime.utcnow().isoformat() + 'Z',
                attachments=self.attachments
        )
