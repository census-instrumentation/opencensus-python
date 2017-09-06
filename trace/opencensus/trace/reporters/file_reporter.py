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

"""Export the trace spans to a local file."""

import json

from opencensus.trace.reporters import base

DEFAULT_FILENAME = 'opencensus-traces.json'


class FileReporter(base.Reporter):
    """
    :type file_name: str
    :param file_name: The name of the output file.
    """

    def __init__(self, file_name=DEFAULT_FILENAME):
        self.file_name = file_name

    def report(self, trace):
        """
        :type trace: dict
        :param trace: Trace collected.
        """
        with open(self.file_name, 'w+') as file:
            trace_str = json.dumps(trace)
            file.write(trace_str)
