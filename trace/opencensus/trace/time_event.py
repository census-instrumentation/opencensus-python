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


class Annotation(object):
    pass


class MessageEvent(object):
    pass


class TimeEvent(object):
    """A collection of TimeEvents. A TimeEvent is a time-stamped annotation on
    the span, consisting of either user-supplied key:value pairs, or details
    of a message sent/received between Spans.
    
    :type timestamp: :class:`~datetime.datetime`
    :param timestamp: The timestamp indicating the time the event occurred.
    
    :type annotation: :class: `~opencensus.trace.time_event.Annotation`
    :param annotation: (Optional) Text annotation with a set of attributes.
    
    :type message_event: :class: `~opencensus.trace.time_event.MessageEvent`
    :param message_event: (Optional) An event describing a message
                          sent/received between Spans.
    """
    def __init__(self, timestamp, annotation=None, message_event=None):
        self.timestamp = timestamp.isoformat() + 'Z'
        self.annotation = annotation
        self.message_event = message_event

    def format_time_event_json(self):
        """Convert a TimeEvent object to json format."""
        time_event = {}

        time_event['time'] = self.timestamp

        if self.annotation is not None:
            time_event['annotation'] = self.annotation

            return time_event

        if self.message_event is not None:
            time_event['message_event'] = self.message_event

            return time_event

        raise ValueError("TimeEvent can contain either an Annotation or a"
                         "MessageEvent object, but not both.")
