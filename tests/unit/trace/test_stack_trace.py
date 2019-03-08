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

import sys
import unittest

import mock

from opencensus.trace import stack_trace as stack_trace_module


class TestStackFrame(unittest.TestCase):
    def test_constructor(self):
        func_name = 'func name'
        original_func_name = 'original func name'
        file_name = 'file name'
        line_num = 10
        col_num = 1
        load_module = 'module'
        build_id = 100
        source_version = 'source version'

        stack_frame = stack_trace_module.StackFrame(
            func_name, original_func_name, file_name, line_num, col_num,
            load_module, build_id, source_version)

        self.assertEqual(stack_frame.func_name, func_name)
        self.assertEqual(stack_frame.original_func_name, original_func_name)
        self.assertEqual(stack_frame.file_name, file_name)
        self.assertEqual(stack_frame.line_num, line_num)
        self.assertEqual(stack_frame.col_num, col_num)
        self.assertEqual(stack_frame.load_module, load_module)
        self.assertEqual(stack_frame.build_id, build_id)
        self.assertEqual(stack_frame.source_version, source_version)

    def test_format_stack_frame_json(self):
        func_name = 'func name'
        original_func_name = 'original func name'
        file_name = 'file name'
        line_num = 10
        col_num = 1
        load_module = 'module'
        build_id = 100
        source_version = 'source version'

        stack_frame = stack_trace_module.StackFrame(
            func_name, original_func_name, file_name, line_num, col_num,
            load_module, build_id, source_version)

        def mock_get_truncatable_str(str):
            return str

        patch = mock.patch('opencensus.trace.stack_trace.get_truncatable_str',
                           mock_get_truncatable_str)

        expected_stack_frame_json = {
            'function_name': func_name,
            'original_function_name': original_func_name,
            'file_name': file_name,
            'line_number': line_num,
            'column_number': col_num,
            'load_module': {
                'module': load_module,
                'build_id': build_id
            },
            'source_version': source_version
        }

        with patch:
            stack_frame_json = stack_frame.format_stack_frame_json()

        self.assertEqual(stack_frame_json, expected_stack_frame_json)


class TestStackTrace(unittest.TestCase):
    def test_constructor_default(self):
        hash_id = 1100
        patch = mock.patch(
            'opencensus.trace.stack_trace.generate_hash_id',
            return_value=hash_id)

        with patch:
            stack_trace = stack_trace_module.StackTrace()

        self.assertEqual(stack_trace.stack_frames, [])
        self.assertEqual(stack_trace.stack_trace_hash_id, hash_id)

    def test_constructor_explicit(self):
        stack_frames = [mock.Mock()]
        hash_id = 1100
        stack_trace = stack_trace_module.StackTrace(stack_frames, hash_id)

        self.assertEqual(stack_trace.stack_frames, stack_frames)
        self.assertEqual(stack_trace.stack_trace_hash_id, hash_id)

    def test_constructor_max_frames(self):
        stack_frames = [mock.Mock()] * (stack_trace_module.MAX_FRAMES + 1)
        stack_trace = stack_trace_module.StackTrace(stack_frames, 100)
        self.assertEqual(stack_trace.dropped_frames_count, 1)
        self.assertEqual(
            len(stack_trace.stack_frames), stack_trace_module.MAX_FRAMES)

    def test_add_stack_frame(self):
        stack_trace = stack_trace_module.StackTrace()
        stack_frame = mock.Mock()
        stack_frame_json = 'test stack frame'
        stack_frame.format_stack_frame_json.return_value = stack_frame_json
        stack_trace.add_stack_frame(stack_frame)

        self.assertEqual(stack_trace.stack_frames, [stack_frame_json])

    def test_format_stack_trace_json_with_stack_frame(self):
        hash_id = 1100
        stack_frame = [mock.Mock()]

        stack_trace = stack_trace_module.StackTrace(
            stack_frames=stack_frame, stack_trace_hash_id=hash_id)

        stack_trace_json = stack_trace.format_stack_trace_json()

        expected_stack_trace_json = {
            'stack_frames': {
                'frame': stack_frame,
                'dropped_frames_count': 0
            },
            'stack_trace_hash_id': hash_id
        }

        self.assertEqual(expected_stack_trace_json, stack_trace_json)

    def test_format_stack_trace_json_without_stack_frame(self):
        hash_id = 1100

        stack_trace = stack_trace_module.StackTrace(
            stack_trace_hash_id=hash_id)

        stack_trace_json = stack_trace.format_stack_trace_json()

        expected_stack_trace_json = {'stack_trace_hash_id': hash_id}

        self.assertEqual(expected_stack_trace_json, stack_trace_json)

    def test_create_from_traceback(self):
        try:
            raise AssertionError('something went wrong')
        except AssertionError:
            _, _, tb = sys.exc_info()

        stack_trace = stack_trace_module.StackTrace.from_traceback(tb)
        self.assertIsNotNone(stack_trace)
        self.assertIsNotNone(stack_trace.stack_trace_hash_id)
        self.assertEqual(len(stack_trace.stack_frames), 1)

        stack_frame = stack_trace.stack_frames[0]
        self.assertEqual(stack_frame['file_name']['value'], __file__)
        self.assertEqual(stack_frame['function_name']['value'],
                         'test_create_from_traceback')
        self.assertEqual(stack_frame['load_module']['module']['value'],
                         __file__)
        self.assertEqual(stack_frame['original_function_name']['value'],
                         'test_create_from_traceback')
        self.assertIsNotNone(stack_frame['source_version']['value'])
        self.assertIsNotNone(stack_frame['load_module']['build_id']['value'])

    def test_dropped_frames(self):
        """Make sure the limit of 128 frames is enforced"""

        def recur(max_depth):
            def _recur_helper(depth):
                if depth >= max_depth:
                    raise AssertionError('reached max depth')
                _recur_helper(depth + 1)

            _recur_helper(0)

        try:
            recur(stack_trace_module.MAX_FRAMES)
        except AssertionError:
            _, _, tb = sys.exc_info()

        stack_trace = stack_trace_module.StackTrace.from_traceback(tb)
        # total frames should be MAX_FRAMES + 3 (1 for test function,
        # 1 for recursion start, one for exception, MAX_FRAMES in helper)
        self.assertEqual(stack_trace.dropped_frames_count, 3)
