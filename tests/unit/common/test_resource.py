# -*- coding: utf-8 -*-

# Copyright 2019, OpenCensus Authors
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

try:
    import mock
except ImportError:
    from unittest import mock

import os
import unittest

from opencensus.common import resource as resource_module
from opencensus.common.resource import Resource


class TestResource(unittest.TestCase):
    def test_init_bad_args(self):
        long_string = (
            "long string is looooooooooooooooooooooooooooooooooooooooooooooooo"
            "ooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo"
            "ooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo"
            "oooooooooooooooooooooooooooooooooooooooooooooooooooooooooooong")
        with self.assertRaises(ValueError):
            Resource('', {})
        with self.assertRaises(ValueError):
            Resource(chr(31), {'key': 'value'})
        with self.assertRaises(ValueError):
            Resource(long_string, {'key': 'value'})
        with self.assertRaises(ValueError):
            Resource('type', {"": 'value'})
        with self.assertRaises(ValueError):
            Resource('type', {None: 'value'})
        with self.assertRaises(ValueError):
            Resource('type', {'key': None})
        with self.assertRaises(ValueError):
            Resource('type', {chr(31): 'value'})
        with self.assertRaises(ValueError):
            Resource('type', {'key': chr(31)})
        with self.assertRaises(ValueError):
            Resource(long_string, {long_string: 'value'})
        with self.assertRaises(ValueError):
            Resource(long_string, {long_string: long_string})
        with self.assertRaises(ValueError):
            Resource('type', {'key1': 'value1', None: 'value2'})
        with self.assertRaises(ValueError):
            Resource('type', {'key1': 'value1', 'key2': None})
        # Empty (but not null) label values are ok
        Resource('type', {'key': ""})

    def test_default_init(self):
        resource = Resource()
        self.assertIsNone(resource.type)
        self.assertIsNotNone(resource.labels)
        self.assertDictEqual(resource.labels, {})

    def test_init(self):
        resource_type = 'type'
        resource_labels = {'key': 'value'}
        resource = Resource(resource_type, resource_labels)
        self.assertEqual(resource.type, resource_type)
        self.assertEqual(resource.labels, resource_labels)
        self.assertIsNot(resource.labels, resource_labels)

    def test_get_type(self):
        resource_type = 'type'
        resource = Resource(resource_type, None)
        self.assertEqual(resource.get_type(), resource_type)

    def test_get_labels(self):
        label_key = 'key'
        label_value = 'value'
        resource_labels = {label_key: label_value}
        resource = Resource('type', resource_labels)
        self.assertEqual(resource.get_labels(), resource_labels)
        self.assertIsNot(resource.get_labels(), resource_labels)
        got_labels = resource.get_labels()
        got_labels[label_key] = mock.Mock()
        self.assertNotEqual(resource.get_labels(), got_labels)
        self.assertEqual(resource.get_labels()[label_key], label_value)

    def test_merge(self):
        r1 = Resource('t1', {'lk1': 'lv1'})
        r2 = Resource('t2', {'lk2': 'lv2'})

        r1m2 = r1.merge(r2)
        self.assertIsNot(r1m2, r1)
        self.assertIsNot(r1m2, r2)
        self.assertEqual(r1m2.type, r1.type)
        self.assertNotEqual(r1m2.type, r2.type)
        self.assertDictEqual(r1m2.labels, {'lk1': 'lv1', 'lk2': 'lv2'})

        r2m1 = r2.merge(r1)
        self.assertIsNot(r2m1, r1)
        self.assertIsNot(r2m1, r2)
        self.assertEqual(r2m1.type, r2.type)
        self.assertNotEqual(r2m1.type, r1.type)
        self.assertDictEqual(r2m1.labels, {'lk1': 'lv1', 'lk2': 'lv2'})

    def test_merge_self(self):
        resource = Resource('type', {'key': 'value'})
        merged = resource.merge(resource)
        self.assertEqual(merged.type, resource.type)
        self.assertDictEqual(merged.labels, resource.labels)

    def test_merge_overwrite(self):
        r1 = Resource('t1', {'lk1': 'lv11'})
        r2 = Resource('t2', {'lk1': 'lv12', 'lk2': 'lv22'})
        self.assertEqual(r1.merge(r2).labels, {'lk1': 'lv11', 'lk2': 'lv22'})
        self.assertEqual(r2.merge(r1).labels, {'lk1': 'lv12', 'lk2': 'lv22'})


class TestResourceModule(unittest.TestCase):

    def test_merge_resource(self):
        with self.assertRaises(ValueError):
            resource_module.merge_resources(None)
        with self.assertRaises(ValueError):
            resource_module.merge_resources([])

        r1 = Resource(None, {'lk1': 'lv11'})
        r2 = Resource('t2', {'lk1': 'lv12', 'lk2': 'lv22'})
        r3 = Resource('t3', {'lk2': 'lv23', 'lk3': 'lv33'})

        merged = resource_module.merge_resources([r1, r2, r3])
        self.assertEqual(merged.type, 't2')
        self.assertDictEqual(
            merged.labels, {'lk1': 'lv11', 'lk2': 'lv22', 'lk3': 'lv33'})

    def test_merge_resource_no_type(self):
        r1 = Resource(None)
        r2 = Resource(None)

        merged = resource_module.merge_resources([r1, r2])
        self.assertEqual(merged.type, None)

    def test_check_ascii_256(self):
        self.assertIsNone(resource_module.check_ascii_256(None))

        # Accept both str and unicode in python 2, reject bytes (i.e. encoded
        # ascii) in python 3.
        self.assertIsNone(resource_module.check_ascii_256(''))
        self.assertIsNone(resource_module.check_ascii_256(u''))
        self.assertIsNone(resource_module.check_ascii_256('abc'))
        self.assertIsNone(resource_module.check_ascii_256(u'abc'))

        with self.assertRaises(ValueError) as ve:
            resource_module.check_ascii_256(u'长猫')
        self.assertIn(u'长', ve.exception.args[0])
        self.assertNotIn(u'猫', ve.exception.args[0])

        with self.assertRaises(ValueError):
            resource_module.check_ascii_256('abc' + chr(31))
        with self.assertRaises(ValueError):
            resource_module.check_ascii_256(u'abc' + chr(31))

    def test_get_from_env(self):
        with mock.patch.dict('os.environ', {
                'OC_RESOURCE_TYPE': 'opencensus.io/example',
                'OC_RESOURCE_LABELS': 'k1=v1,k2=v2'
        }):
            resource = resource_module.get_from_env()
        self.assertEqual(resource.type, 'opencensus.io/example')
        self.assertDictEqual(resource.labels, {'k1': 'v1', 'k2': 'v2'})

    def test_get_from_env_no_type(self):
        with mock.patch.dict('os.environ', {
                'OC_RESOURCE_LABELS': 'k1=v1,k2=v2'
        }):
            try:
                del os.environ['OC_RESOURCE_TYPE']
            except KeyError:
                pass
            self.assertIsNone(resource_module.get_from_env())

    def test_get_from_env_no_labels(self):
        with mock.patch.dict('os.environ', {
                'OC_RESOURCE_TYPE': 'opencensus.io/example',
        }):
            try:
                del os.environ['OC_RESOURCE_LABELS']
            except KeyError:
                pass
            resource = resource_module.get_from_env()
        self.assertEqual(resource.type, 'opencensus.io/example')
        self.assertDictEqual(resource.labels, {})

    def test_get_from_env_outer_spaces(self):
        with mock.patch.dict('os.environ', {
                'OC_RESOURCE_TYPE': ' opencensus.io/example  ',
                'OC_RESOURCE_LABELS': 'k1= v1 ,  k2=v2  '
        }):
            resource = resource_module.get_from_env()
        self.assertEqual(resource.type, 'opencensus.io/example')
        self.assertDictEqual(resource.labels, {'k1': 'v1', 'k2': 'v2'})

    def test_get_from_env_inner_spaces(self):
        # Spaces inside key/label values should be contained by quotes, refuse
        # to parse this.
        with mock.patch.dict('os.environ', {
                'OC_RESOURCE_TYPE': 'opencensus.io / example',
                'OC_RESOURCE_LABELS': 'key one=value one,  key two= value two'
        }):
            resource = resource_module.get_from_env()
        self.assertEqual(resource.type, 'opencensus.io / example')
        self.assertDictEqual(resource.labels, {})

    def test_get_from_env_quoted_chars(self):
        with mock.patch.dict('os.environ', {
                'OC_RESOURCE_TYPE': 'opencensus.io/example',
                'OC_RESOURCE_LABELS': '"k1=\'"="v1,,,", "k2"=\'="=??\''
        }):
            resource = resource_module.get_from_env()
        self.assertDictEqual(resource.labels, {"k1='": 'v1,,,', 'k2': '="=??'})

    def test_parse_labels(self):
        self.assertEqual(resource_module.parse_labels("k1=v1"), {'k1': 'v1'})
        self.assertEqual(
            resource_module.parse_labels("k1=v1,k2=v2"),
            {'k1': 'v1', 'k2': 'v2'})

        self.assertEqual(
            resource_module.parse_labels('k1="v1"'),
            {'k1': 'v1'})

        self.assertEqual(
            resource_module.parse_labels('k1="v1==,"'),
            {'k1': 'v1==,'})

        self.assertEqual(
            resource_module.parse_labels('k1="one/two/three"'),
            {'k1': 'one/two/three'})

        self.assertEqual(
            resource_module.parse_labels('k1="one\\two\\three"'),
            {'k1': 'one\\two\\three'})

        with mock.patch('opencensus.common.resource.logger') as mock_logger:
            resource_module.parse_labels('k1=v1, k2=v2, k1=v3')
        mock_logger.warning.assert_called_once()
