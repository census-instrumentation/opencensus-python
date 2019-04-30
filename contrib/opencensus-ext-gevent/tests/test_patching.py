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

import unittest

import opencensus.common.runtime_context as runtime_context
import gevent.monkey

import mock


class TestPatching(unittest.TestCase):
    def setUp(self):
        self.original_context = runtime_context.RuntimeContext

    def tearDown(self):
        runtime_context.RuntimeContext = self.original_context

    @mock.patch("gevent.monkey.is_module_patched", return_value=False)
    def test_context_is_switched_without_contextvar_support(
        self, patched_is_module_patched
    ):
        # patched_is_module_patched.return_value = False

        # Trick gevent into thinking it is run for the first time.
        # Allows to run multiple tests.
        gevent.monkey.saved = {}

        # All module patching is disabled to avoid the need of "unpatching".
        # The needed events are emitted nevertheless.
        gevent.monkey.patch_all(
            contextvar=False,
            socket=False,
            dns=False,
            time=False,
            select=False,
            thread=False,
            os=False,
            ssl=False,
            httplib=False,
            subprocess=False,
            sys=False,
            aggressive=False,
            Event=False,
            builtins=False,
            signal=False,
            queue=False
        )

        assert isinstance(
            runtime_context.RuntimeContext,
            runtime_context._ThreadLocalRuntimeContext,
        )

    @mock.patch("gevent.monkey.is_module_patched", return_value=True)
    def test_context_is_switched_with_contextvar_support(
        self, patched_is_module_patched
    ):

        # Trick gevent into thinking it is run for the first time.
        # Allows to run multiple tests.
        gevent.monkey.saved = {}

        # All module patching is disabled to avoid the need of "unpatching".
        # The needed events are emitted nevertheless.
        gevent.monkey.patch_all(
            contextvar=False,
            socket=False,
            dns=False,
            time=False,
            select=False,
            thread=False,
            os=False,
            ssl=False,
            httplib=False,
            subprocess=False,
            sys=False,
            aggressive=False,
            Event=False,
            builtins=False,
            signal=False,
            queue=False
        )

        assert runtime_context.RuntimeContext is self.original_context
