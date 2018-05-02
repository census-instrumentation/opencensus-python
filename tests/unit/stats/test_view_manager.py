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
from opencensus.stats import view_manager as view_manager_module


class TestViewManager(unittest.TestCase):
    def test_constructor(self):
        view_manager = view_manager_module.ViewManager()

        self.assertIsNotNone(view_manager.time)
        self.assertIsNotNone(view_manager.measure_to_view_map)

    def test_register_view(self):
        '''finish'''