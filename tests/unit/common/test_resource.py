# Copyright 2019 Google Inc.
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
    from mock import Mock
except ImportError:
    from unittest.mock import Mock

import unittest

from opencensus.common.resource import Resource


class TestResource(unittest.TestCase):
    def test_init_bad_args(self):
        with self.assertRaises(ValueError):
            Resource("", Mock())
        with self.assertRaises(ValueError):
            Resource(Mock(), {"": Mock()})
        with self.assertRaises(ValueError):
            Resource(Mock(), {None: Mock()})
        with self.assertRaises(ValueError):
            Resource(Mock(), {Mock(): None})
        with self.assertRaises(ValueError):
            Resource(Mock(), {Mock(): Mock(), None: Mock()})
        with self.assertRaises(ValueError):
            Resource(Mock(), {Mock(): Mock(), Mock(): None})
        # Empty (but not null) label values are ok
        Resource(Mock(), {Mock(): ""})

    def test_default_init(self):
        resource = Resource()
        self.assertIsNone(resource.type)
        self.assertIsNotNone(resource.labels)
        self.assertDictEqual(resource.labels, {})

    def test_init(self):
        resource_type = Mock()
        resource_labels = {Mock(): Mock()}
        resource = Resource(resource_type, resource_labels)
        self.assertEqual(resource.type, resource_type)
        self.assertEqual(resource.labels, resource_labels)
        self.assertIsNot(resource.labels, resource_labels)

    def test_get_type(self):
        resource_type = Mock()
        resource = Resource(resource_type, None)
        self.assertEqual(resource.get_type(), resource_type)

    def test_get_labels(self):
        label_key = Mock()
        label_value = Mock()
        resource_labels = {label_key: label_value}
        resource = Resource(Mock(), resource_labels)
        self.assertEqual(resource.get_labels(), resource_labels)
        self.assertIsNot(resource.get_labels(), resource_labels)
        got_labels = resource.get_labels()
        got_labels[label_key] = Mock()
        self.assertNotEqual(resource.get_labels(), got_labels)
        self.assertEqual(resource.get_labels()[label_key], label_value)

    def test_merge(self):
        t1, lk1, lv1 = Mock(), Mock(), Mock()
        t2, lk2, lv2 = Mock(), Mock(), Mock()
        r1 = Resource(t1, {lk1: lv1})
        r2 = Resource(t2, {lk2: lv2})

        r1m2 = r1.merge(r2)
        self.assertIsNot(r1m2, r1)
        self.assertIsNot(r1m2, r2)
        self.assertEqual(r1m2.type, r1.type)
        self.assertNotEqual(r1m2.type, r2.type)
        self.assertDictEqual(r1m2.labels, {lk1: lv1, lk2: lv2})

        r2m1 = r2.merge(r1)
        self.assertIsNot(r2m1, r1)
        self.assertIsNot(r2m1, r2)
        self.assertEqual(r2m1.type, r2.type)
        self.assertNotEqual(r2m1.type, r1.type)
        self.assertDictEqual(r2m1.labels, {lk1: lv1, lk2: lv2})

    def test_merge_self(self):
        resource = Resource(Mock(), {Mock(): Mock()})
        merged = resource.merge(resource)
        self.assertEqual(merged.type, resource.type)
        self.assertDictEqual(merged.labels, resource.labels)

    def test_merge_overwrite(self):
        r1 = Resource(Mock(), {'lk1': 'lv11'})
        r2 = Resource(Mock(), {'lk1': 'lv12', 'lk2': 'lv22'})
        self.assertEqual(r1.merge(r2).labels, {'lk1': 'lv11', 'lk2': 'lv22'})
        self.assertEqual(r2.merge(r1).labels, {'lk1': 'lv12', 'lk2': 'lv22'})
