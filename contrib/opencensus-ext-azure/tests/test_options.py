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

import os
import unittest

from opencensus.ext.azure import common


class TestOptions(unittest.TestCase):
    def setUp(self):
        os.environ.clear()

    def test_process_options_ikey_code_cs(self):
        options = common.Options()
        options.connection_string = 'Authorization=ikey;InstrumentationKey=123'
        options.instrumentation_key = '456'
        os.environ['APPLICATIONINSIGHTS_CONNECTION_STRING'] = \
            'Authorization=ikey;InstrumentationKey=789'
        os.environ['APPINSIGHTS_INSTRUMENTATIONKEY'] = '101112'
        common.process_options(options)

        self.assertEqual(options.instrumentation_key, '123')

    def test_process_options_ikey_code_ikey(self):
        options = common.Options()
        options.connection_string = None
        options.instrumentation_key = '456'
        os.environ['APPLICATIONINSIGHTS_CONNECTION_STRING'] = \
            'Authorization=ikey;InstrumentationKey=789'
        os.environ['APPINSIGHTS_INSTRUMENTATIONKEY'] = '101112'
        common.process_options(options)

        self.assertEqual(options.instrumentation_key, '456')

    def test_process_options_ikey_env_cs(self):
        options = common.Options()
        options.connection_string = None
        options.instrumentation_key = None
        os.environ['APPLICATIONINSIGHTS_CONNECTION_STRING'] = \
            'Authorization=ikey;InstrumentationKey=789'
        os.environ['APPINSIGHTS_INSTRUMENTATIONKEY'] = '101112'
        common.process_options(options)

        self.assertEqual(options.instrumentation_key, '789')

    def test_process_options_ikey_env_ikey(self):
        options = common.Options()
        options.connection_string = None
        options.instrumentation_key = None
        os.environ['APPINSIGHTS_INSTRUMENTATIONKEY'] = '101112'
        common.process_options(options)

        self.assertEqual(options.instrumentation_key, '101112')

    def test_process_options_endpoint_code_cs(self):
        options = common.Options()
        options.connection_string = 'Authorization=ikey;IngestionEndpoint=123'
        os.environ['APPLICATIONINSIGHTS_CONNECTION_STRING'] = \
            'Authorization=ikey;IngestionEndpoint=456'
        common.process_options(options)

        self.assertEqual(options.endpoint, '123')

    def test_process_options_endpoint_env_cs(self):
        options = common.Options()
        options.connection_string = None
        os.environ['APPLICATIONINSIGHTS_CONNECTION_STRING'] = \
            'Authorization=ikey;IngestionEndpoint=456'
        common.process_options(options)

        self.assertEqual(options.endpoint, '456')

    def test_process_options_endpoint_default(self):
        options = common.Options()
        options.connection_string = None
        common.process_options(options)

        self.assertEqual(options.endpoint,
                         'https://dc.services.visualstudio.com')

    def test_process_options_proxies_default(self):
        options = common.Options()
        options.proxies = "{}"
        common.process_options(options)

        self.assertEqual(options.proxies, "{}")

    def test_process_options_proxies_set_proxies(self):
        options = common.Options()
        options.connection_string = None
        options.proxies = '{"https": "https://test-proxy.com"}'
        common.process_options(options)

        self.assertEqual(
            options.proxies,
            '{"https": "https://test-proxy.com"}'
        )

    def test_parse_connection_string_none(self):
        cs = None
        result = common.parse_connection_string(cs)

        self.assertEqual(result, {})

    def test_parse_connection_string_invalid(self):
        cs = 'asd'
        self.assertRaises(ValueError,
                          lambda: common.parse_connection_string(cs))

    def test_parse_connection_string_default_auth(self):
        cs = 'InstrumentationKey=123'
        result = common.parse_connection_string(cs)
        self.assertEqual(result['instrumentationkey'], '123')

    def test_parse_connection_string_invalid_auth(self):
        cs = 'Authorization=asd'
        self.assertRaises(ValueError,
                          lambda: common.parse_connection_string(cs))

    def test_parse_connection_string_explicit_endpoint(self):
        cs = 'Authorization=ikey;IngestionEndpoint=123;' \
            'Location=us;EndpointSuffix=suffix'
        result = common.parse_connection_string(cs)

        self.assertEqual(result['ingestionendpoint'], '123')

    def test_parse_connection_string_default(self):
        cs = 'Authorization=ikey;Location=us'
        result = common.parse_connection_string(cs)

        self.assertEqual(result['ingestionendpoint'],
                         None)

    def test_parse_connection_string_no_location(self):
        cs = 'Authorization=ikey;EndpointSuffix=suffix'
        result = common.parse_connection_string(cs)

        self.assertEqual(result['ingestionendpoint'], 'https://dc.suffix')

    def test_parse_connection_string_location(self):
        cs = 'Authorization=ikey;EndpointSuffix=suffix;Location=us'
        result = common.parse_connection_string(cs)

        self.assertEqual(result['ingestionendpoint'], 'https://us.dc.suffix')
