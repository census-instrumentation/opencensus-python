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

import mock
import unittest

from opencensus.ext.pyramid import config


class TestPyramidTraceSettings(unittest.TestCase):
    def test_trace_settings_default(self):
        registry = mock.Mock()
        registry.settings = {}
        trace_settings = config.PyramidTraceSettings(registry)

        default_config = config.DEFAULT_PYRAMID_TRACER_CONFIG
        assert trace_settings.SAMPLER == default_config['SAMPLER']
        assert trace_settings.EXPORTER == default_config['EXPORTER']
        assert trace_settings.PROPAGATOR == default_config['PROPAGATOR']

        default_params = config.DEFAULT_PYRAMID_TRACER_PARAMS
        assert trace_settings.params['BLACKLIST_PATHS'] == default_params[
            'BLACKLIST_PATHS']

    def test_trace_settings_override(self):
        mock_sampler = mock.Mock()
        mock_exporter = mock.Mock()
        mock_propagator = mock.Mock()
        mock_blacklist_paths = ['foo/bar']

        registry = mock.Mock()
        registry.settings = {
            'OPENCENSUS_TRACE': {
                'SAMPLER': mock_sampler,
                'EXPORTER': mock_exporter,
                'PROPAGATOR': mock_propagator,
            },
            'OPENCENSUS_TRACE_PARAMS': {
                'BLACKLIST_PATHS': mock_blacklist_paths,
            }
        }

        trace_settings = config.PyramidTraceSettings(registry)

        assert trace_settings.SAMPLER == mock_sampler
        assert trace_settings.EXPORTER == mock_exporter
        assert trace_settings.PROPAGATOR == mock_propagator

        assert trace_settings.params['BLACKLIST_PATHS'] == mock_blacklist_paths

    def test_trace_settings_invalid(self):
        registry = mock.Mock()
        registry.settings = {}

        trace_settings = config.PyramidTraceSettings(registry)

        with self.assertRaises(AttributeError):
            trace_settings.INVALID
