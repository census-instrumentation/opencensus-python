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

import datetime
import unittest

import mock

from opencensus.common import utils
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


class TestMessageEvent(unittest.TestCase):
    def test_constructor_default(self):
        id = '1234'

        message_event = time_event_module.MessageEvent(id)

        self.assertEqual(message_event.id, id)
        self.assertEqual(message_event.type,
                         time_event_module.Type.TYPE_UNSPECIFIED)
        self.assertIsNone(message_event.uncompressed_size_bytes)
        self.assertIsNone(message_event.compressed_size_bytes)

    def test_constructor_explicit(self):
        id = '1234'
        type = time_event_module.Type.SENT
        uncompressed_size_bytes = '100'

        message_event = time_event_module.MessageEvent(
            id, type, uncompressed_size_bytes)

        self.assertEqual(message_event.id, id)
        self.assertEqual(message_event.type, type)
        self.assertEqual(message_event.uncompressed_size_bytes,
                         uncompressed_size_bytes)
        self.assertEqual(message_event.compressed_size_bytes,
                         uncompressed_size_bytes)

    def test_format_message_event_json(self):
        id = '1234'
        type = time_event_module.Type.SENT
        uncompressed_size_bytes = '100'

        message_event = time_event_module.MessageEvent(
            id, type, uncompressed_size_bytes)

        expected_message_event_json = {
            'type': type,
            'id': id,
            'uncompressed_size_bytes': uncompressed_size_bytes,
            'compressed_size_bytes': uncompressed_size_bytes
        }

        message_event_json = message_event.format_message_event_json()

        self.assertEqual(expected_message_event_json, message_event_json)

    def test_format_message_event_json_no_size(self):
        id = '1234'
        type = time_event_module.Type.SENT

        message_event = time_event_module.MessageEvent(id, type)

        expected_message_event_json = {
            'type': type,
            'id': id,
        }

        message_event_json = message_event.format_message_event_json()

        self.assertEqual(expected_message_event_json, message_event_json)


class TestTimeEvent(unittest.TestCase):
    def test_constructor(self):
        timestamp = datetime.datetime.utcnow()
        message_event = mock.Mock()

        time_event = time_event_module.TimeEvent(
            timestamp=timestamp, message_event=message_event)

        self.assertEqual(time_event.timestamp, utils.to_iso_str(timestamp))
        self.assertEqual(time_event.message_event, message_event)

    def test_constructor_value_error(self):

        timestamp = datetime.datetime.utcnow()
        annotation = mock.Mock()
        message_event = mock.Mock()

        with self.assertRaises(ValueError):
            time_event_module.TimeEvent(
                timestamp=timestamp,
                annotation=annotation,
                message_event=message_event)

    def test_format_time_event_json_annotation(self):
        timestamp = datetime.datetime.utcnow()
        mock_annotation = 'test annotation'
        annotation = mock.Mock()
        annotation.format_annotation_json.return_value = mock_annotation

        time_event = time_event_module.TimeEvent(
            timestamp=timestamp, annotation=annotation)

        time_event_json = time_event.format_time_event_json()
        expected_time_event_json = {
            'time': utils.to_iso_str(timestamp),
            'annotation': mock_annotation
        }

        self.assertEqual(time_event_json, expected_time_event_json)

    def test_format_time_event_json_message_event(self):
        timestamp = datetime.datetime.utcnow()
        mock_message_event = 'test annotation'
        message_event = mock.Mock()
        message_event.format_message_event_json.return_value = \
            mock_message_event

        time_event = time_event_module.TimeEvent(
            timestamp=timestamp, message_event=message_event)

        time_event_json = time_event.format_time_event_json()
        expected_time_event_json = {
            'time': utils.to_iso_str(timestamp),
            'message_event': mock_message_event
        }

        self.assertEqual(time_event_json, expected_time_event_json)
