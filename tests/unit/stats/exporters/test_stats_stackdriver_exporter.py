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
from opencensus.stats.exporters import stackdriver_exporter as stackdriver_exporter_module


class _Client(object):
    '''
    def __init__(self, project=None, resource=None):
        if project is None:
            project = 'PROJECT'

        self.project = project
        self.resource = ('global', {})
    '''

class TestStackDriverExporter(unittest.TestCase):

    def test_constructor_defaults(self):
        '''
        patch = mock.patch(
            'opencensus.stats.exporters.stackdriver_exporter.Client',
            new=_Client)

        with patch:
            exporter = stackdriver_exporter_module.StackDriverExporter()

        project_id = 'PROJECT'
        self.assertEqual(exporter.project_id, project_id)
        self.assertEqual(_Client(project='PROJECT'), exporter.client)
        '''

    def test_constructor_explicit(self):
        ''' finish me '''

    def test_emit(self):
        ''' finish me '''

    def test_set_resource(self):
        ''' finish me'''

    def test_translate_to_stackdriver(self):
        ''' finish me '''
