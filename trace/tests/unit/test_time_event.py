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

import unittest

import mock

from opencensus.trace import time_event as time_event_module


class TestAnnotation(unittest.TestCase):
    def test_constructor(self):
        description = 'test description'
        attributes = mock.Mock()

        annotation = time_event_module.Annotation(description, attributes)

        self.assertEqual(annotation.description, description)
        self.assertEqual(annotation.attributes, attributes)

    def test_format_annotation_json_with_attributes(self):
        description = 'test description'
        attrs_json = {}
        attributes = mock.Mock()
        attributes.format_attributes_json.return_value = attrs_json

        annotation = time_event_module.Annotation(description, attributes)

        annotation_json = annotation.format_annotation_json()

        expected_annotation_json = {
            'description': {
                'value': description,
                'truncated_byte_count': 0
            },
            'attributes': {}
        }

        self.assertEqual(annotation_json, expected_annotation_json)

    def test_format_annotation_json_without_attributes(self):
        description = 'test description'

        annotation = time_event_module.Annotation(description)

        annotation_json = annotation.format_annotation_json()

        expected_annotation_json = {
            'description': {
                'value': description,
                'truncated_byte_count': 0
            }
        }

        self.assertEqual(annotation_json, expected_annotation_json)


class TestTimeEvent(unittest.TestCase):
    def test_constructor(self):
        import datetime

        timestamp = datetime.datetime.utcnow()
        annotation = mock.Mock()

        time_event =  time_event_module.TimeEvent(
            timestamp=timestamp,
            annotation=annotation)

        self.assertEqual(time_event.timestamp, timestamp.isoformat() + 'Z')
        self.assertEqual(time_event.annotation, annotation)

    def test_format_time_event_json(self):
        import datetime

        timestamp = datetime.datetime.utcnow()
        mock_annotation = 'test annotation'
        annotation = mock.Mock()
        annotation.format_annotation_json.return_value = mock_annotation

        time_event = time_event_module.TimeEvent(
            timestamp=timestamp,
            annotation=annotation)

        time_event_json = time_event.format_time_event_json()
        expected_time_event_json = {
            'time': timestamp.isoformat() + 'Z',
            'annotation': mock_annotation
        }

        self.assertEqual(time_event_json, expected_time_event_json)
