# Copyright 2017 Google Inc.
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


class FileReporter(object):
    """
    :type file_name: str
    :param file_name: The name of the output file.
    """

    def __init__(self, file_name):
        self.file_name = file_name

    def report(self, traces):
        """Report the traces by printing it out.

        :type traces: dict
        :param traces: Traces collected.
        """
        with open(self.file_name, 'w+') as file:
            traces_str = json.dumps(traces)
            file.write(traces_str)
