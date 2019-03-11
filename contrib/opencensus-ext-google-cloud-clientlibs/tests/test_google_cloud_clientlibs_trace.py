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

from opencensus.ext.google_cloud_clientlibs import trace


class Test_google_cloud_clientlibs_trace(unittest.TestCase):
    def test_trace_integration(self):
        mock_trace_grpc = mock.Mock()
        mock_trace_http = mock.Mock()

        patch_trace_grpc = mock.patch(
            'opencensus.ext.google_cloud_clientlibs.trace.trace_grpc',
            mock_trace_grpc)
        patch_trace_http = mock.patch(
            'opencensus.ext.google_cloud_clientlibs.trace.trace_http',
            mock_trace_http)

        with patch_trace_grpc, patch_trace_http:
            trace.trace_integration()

        self.assertTrue(mock_trace_grpc.called)
        self.assertTrue(mock_trace_http.called)

    def test_trace_grpc(self):
        mock_wrap = mock.Mock()
        mock__helpers = mock.Mock()

        wrap_result = 'wrap result'
        mock_wrap.return_value = wrap_result

        mock_make_secure_channel_func = mock.Mock()
        mock_make_secure_channel_func.__name__ = 'make_secure_channel'
        setattr(mock__helpers, 'make_secure_channel',
                mock_make_secure_channel_func)

        patch_wrap = mock.patch(
            'opencensus.ext.google_cloud_clientlibs.trace'
            '.wrap_make_secure_channel', mock_wrap)
        patch__helpers = mock.patch(
            'opencensus.ext.google_cloud_clientlibs.trace._helpers',
            mock__helpers)

        with patch_wrap, patch__helpers:
            trace.trace_integration()

        self.assertEqual(
            getattr(mock__helpers, 'make_secure_channel'), wrap_result)

    def test_trace_http(self):
        mock_trace_requests = mock.Mock()
        patch = mock.patch(
            'opencensus.ext.google_cloud_clientlibs.trace'
            '.trace_requests', mock_trace_requests)

        with patch:
            trace.trace_http()

        self.assertTrue(mock_trace_requests.called)

    def test_wrap_make_secure_channel(self):
        mock_interceptor = mock.Mock()
        mock_func = mock.Mock()

        patch_interceptor = mock.patch(
            'opencensus.ext.google_cloud_clientlibs.trace'
            '.OpenCensusClientInterceptor', mock_interceptor)

        wrapped = trace.wrap_make_secure_channel(mock_func)

        with patch_interceptor:
            wrapped()

        self.assertTrue(mock_interceptor.called)

    def test_wrap_insecure_channel(self):
        mock_interceptor = mock.Mock()
        mock_func = mock.Mock()

        patch_interceptor = mock.patch(
            'opencensus.ext.google_cloud_clientlibs.trace'
            '.OpenCensusClientInterceptor', mock_interceptor)

        wrapped = trace.wrap_insecure_channel(mock_func)

        with patch_interceptor:
            wrapped()

        self.assertTrue(mock_interceptor.called)

    def test_wrap_create_channel(self):
        mock_interceptor = mock.Mock()
        mock_func = mock.Mock()

        patch_interceptor = mock.patch(
            'opencensus.ext.google_cloud_clientlibs.trace'
            '.OpenCensusClientInterceptor', mock_interceptor)

        wrapped = trace.wrap_create_channel(mock_func)

        with patch_interceptor:
            wrapped()

        self.assertTrue(mock_interceptor.called)
