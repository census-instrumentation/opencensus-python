# Copyright 2017, OpenCensus Authors
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

from opencensus.trace.utils import _get_truncatable_str


class Annotation(object):
    """Text annotation with a set of attributes.

    :type description: str
    :param description: A user-supplied message describing the event.
                        The maximum length for the description is 256 bytes.

    :type attributes: :class:`~opencensus.trace.attributes.Attributes`
    :param attributes: A set of attributes on the annotation.
                       You can have up to 4 attributes per Annotation.
    """
    def __init__(self, description, attributes=None):
        self.description = description
        self.attributes = attributes

    def format_annotation_json(self):
        annotation_json = {}
        annotation_json['description'] = _get_truncatable_str(self.description)

        if self.attributes is not None:
            annotation_json['attributes'] = self.attributes.\
                format_attributes_json()

        return annotation_json


class TimeEvent(object):
    """A collection of TimeEvents. A TimeEvent is a time-stamped annotation on
    the span, consisting of either user-supplied key:value pairs, or details
    of a message sent/received between Spans.

    :type timestamp: :class:`~datetime.datetime`
    :param timestamp: The timestamp indicating the time the event occurred.

    :type annotation: :class: `~opencensus.trace.time_event.Annotation`
    :param annotation: (Optional) Text annotation with a set of attributes.
    """
    def __init__(self, timestamp, annotation):
        self.timestamp = timestamp.isoformat() + 'Z'
        self.annotation = annotation

    def format_time_event_json(self):
        """Convert a TimeEvent object to json format."""
        time_event = {}
        time_event['time'] = self.timestamp
        time_event['annotation'] = self.annotation.format_annotation_json()

        return time_event
