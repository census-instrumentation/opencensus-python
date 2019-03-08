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

from opencensus.trace import attributes as attributes_module


class TestAttributes(unittest.TestCase):
    def test_constructor_default(self):
        attributes = attributes_module.Attributes()
        self.assertEqual(attributes.attributes, {})

    def test_constructor_explicit(self):
        attr = {'key': 'value'}
        attributes = attributes_module.Attributes(attr)

        self.assertEqual(attributes.attributes, attr)

    def test_set_attribute(self):
        key = 'test key'
        value = 'test value'
        attributes = attributes_module.Attributes()
        attributes.set_attribute(key=key, value=value)

        expected_attr = {key: value}

        self.assertEqual(expected_attr, attributes.attributes)

    def test_delete_attribute(self):
        attr = {'key1': 'value1', 'key2': 'value2'}
        attributes = attributes_module.Attributes(attr)
        attributes.delete_attribute('key1')

        self.assertEqual(attributes.attributes, {'key2': 'value2'})

    def test_get_attribute(self):
        attr = {'key': 'value'}
        attributes = attributes_module.Attributes(attr)
        value = attributes.get_attribute('key')

        self.assertEqual(value, 'value')

    def test_format_attributes_json(self):
        attrs = {
            'key1': 'test string',
            'key2': True,
            'key3': 100,
            'key4': 123.456,
        }

        attributes = attributes_module.Attributes(attrs)
        attributes_json = attributes.format_attributes_json()

        expected_attributes_json = {
            'attributeMap': {
                'key1': {
                    'string_value': {
                        'value': 'test string',
                        'truncated_byte_count': 0
                    }
                },
                'key2': {
                    'bool_value': True
                },
                'key3': {
                    'int_value': 100
                },
                'key4': {
                    'double_value': 123.456
                }
            }
        }

        self.assertEqual(expected_attributes_json, attributes_json)

    def test_format_attributes_json_type_error(self):
        attrs = {
            'key1': mock.Mock(),
        }

        expected_json = {'attributeMap': {}}

        attributes = attributes_module.Attributes(attrs)
        attributes_json = attributes.format_attributes_json()

        self.assertEqual(attributes_json, expected_json)
