import unittest
import mock
from opencensus.tags import tag_map as tag_map_module

class TestTagMap(unittest.TestCase):

    def test_constructor_defaults(self):
        tag_map = tag_map_module.TagMap()
        self.assertEqual(tag_map.tags, {})
        self.assertEqual(tag_map.map, {})

    def test_constructor_explicit(self):
        tags = [{'key1':'value1'}]
        map = {}

        tag_map = tag_map_module.TagMap(tags=tags, map=map)
        self.assertEqual(tag_map.tags, tags)
        self.assertEqual(tag_map.map, map)

    def test_insert(self):
        test_key = 'key1'
        test_value = 'value1'
        tag_map = tag_map_module.TagMap()
        tag_map.insert(key=test_key, value=test_value)
        self.assertEqual(tag_map[test_key], test_value)

    def test_delete(self):
        key = 'key1'
        tag_map = tag_map_module.TagMap(tags={key:'value1'})
        tag_map.delete(key)
        self.assertTrue(key not in tag_map)

    def test_update(self):
        key = 'key1'
        value = 'value1'
        tag_map = tag_map_module.TagMap(tags={key: 'value2'})
        tag_map.update(key=key, value=value)
        expected_val = tag_map.__getattribute__(value)
        self.assertEqual(expected_val, value)

    def test_tag_key_exits(self):
        key = mock.Mock()
        value = mock.Mock()
        tag_map = tag_map_module.TagMap(tags={key: value})
        self.assertTrue(tag_map.tag_key_exits(key))
        self.assertFalse(tag_map.tag_key_exits('nokey'))

    def test_value(self):
        key = 'key1'
        value = 'value1'
        tag_map = tag_map_module.TagMap(tags={key: value})
        test_val = tag_map.get_value(key)
        self.assertEqual(test_val, value)