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

import random

from opencensus.trace.utils import _get_truncatable_str


class StackFrame(object):
    """Represents a single stack frame in a stack trace.

    :type func_name: str
    :param func_name: The fully-qualified name that uniquely identifies the
                      function or method that is active in this frame (up to
                      1024 bytes).

    :type original_func_name: str
    :param original_func_name: An un-mangled function name, if functionName is
                               mangled. The name can be fully-qualified
                               (up to 1024 bytes).

    :type file_name: str
    :param file_name: The name of the source file where the function call
                      appears (up to 256 bytes).

    :type line_num: int
    :param line_num: The line number in fileName where the function call
                     appears.

    :type col_num: int
    :param col_num: The column number where the function call appears, if
                    available. This is important in JavaScript because of its
                    anonymous functions.

    :type load_module: str
    :param load_module: For example: main binary, kernel modules, and dynamic
                        libraries such as libc.so, sharedlib.so
                        (up to 256 bytes).

    :type build_id: str
    :param build_id: A unique identifier for the module, usually a hash of its
                    contents (up to 128 bytes).


    :type source_version: str
    :param source_version: The version of the deployed source code
                           (up to 128 bytes).
    """
    def __init__(self,
                 func_name,
                 original_func_name,
                 file_name,
                 line_num,
                 col_num,
                 load_module,
                 build_id,
                 source_version):
        self.func_name = func_name
        self.original_func_name = original_func_name
        self.file_name = file_name
        self.line_num = line_num
        self.col_num = col_num
        self.load_module = load_module
        self.build_id = build_id
        self.source_version = source_version

    def format_stack_frame_json(self):
        """Convert StackFrame object to json format."""
        stack_frame_json = {}
        stack_frame_json['function_name'] = _get_truncatable_str(
            self.func_name)
        stack_frame_json['original_function_name'] = _get_truncatable_str(
            self.original_func_name)
        stack_frame_json['file_name'] = _get_truncatable_str(self.file_name)
        stack_frame_json['line_number'] = self.line_num
        stack_frame_json['col_number'] = self.col_num
        stack_frame_json['load_module'] = {
            'module': _get_truncatable_str(self.load_module),
            'build_id': _get_truncatable_str(self.build_id),
        }
        stack_frame_json['source_version'] = _get_truncatable_str(
            self.source_version)

        return stack_frame_json


class StackTrace(object):
    """A call stack appearing in a trace.

    :type stack_frames: list
    :param stack_frames: Stack frames in this stack trace. A maximum of 128
                         frames are allowed.

    :type stack_trace_hash_id: str
    :param stack_trace_hash_id: The hash ID is used to conserve network
                                bandwidth for duplicate stack traces within a
                                single trace.
    """
    def __init__(self, stack_frames=None, stack_trace_hash_id=None):
        if stack_frames is None:
            stack_frames = []

        if stack_trace_hash_id is None:
            stack_trace_hash_id = generate_hash_id()

        self.stack_frames = stack_frames
        self.stack_trace_hash_id = stack_trace_hash_id

    def add_stack_frame(self, stack_frame):
        """Add StackFrame to frames list."""
        self.stack_frames.append(stack_frame.format_stack_frame_json())

    def format_stack_trace_json(self):
        """Convert a StackTrace object to json format."""
        stack_trace_json = {}

        if self.stack_frames:
            stack_trace_json['stack_frames'] = self.stack_frames

        stack_trace_json['stack_trace_hash_id'] = self.stack_trace_hash_id

        return stack_trace_json


def generate_hash_id():
    """Generate a hash id."""
    return random.getrandbits(64)
