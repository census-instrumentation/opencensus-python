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

import unittest
import mock
from datetime import datetime
from opencensus.stats import measure_to_view_map as measure_to_view_map_module


class TestMeasureToViewMap(unittest.TestCase):

    def test_constructor(self):
        measure_to_view_map = measure_to_view_map_module.MeasureToViewMap()

        self.assertEqual({}, measure_to_view_map._map)
        self.assertEqual({}, measure_to_view_map._registered_views)
        self.assertEqual({}, measure_to_view_map._registered_measures)
        self.assertEqual(set(), measure_to_view_map._exported_views)

    """
    def test_get_view(self):
        view_name = 'testView'
        timestamp = datetime.utcnow().isoformat() + 'Z'
        measure_to_view_map = measure_to_view_map_module.MeasureToViewMap()

        measure_to_view_map._registered_views = {}
        no_registered_views = measure_to_view_map.get_view(view_name=view_name, timestamp=timestamp)
        self.assertEqual(None, no_registered_views)

        measure_to_view_map._registered_views = {'testView': 'test'}
        with_registered_views = measure_to_view_map.get_view(view_name=view_name, timestamp=timestamp)
        self.assertIsNotNone(with_registered_views)"""