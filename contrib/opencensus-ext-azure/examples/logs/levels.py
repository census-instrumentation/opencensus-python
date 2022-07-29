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

import logging

class RootFilter(logging.Filter):

    def filter(self, record):
        if record.name == "root":
            record.msg = "ROOT LOG: " + record.msg
        else:
            record.msg = "CHILD LOG: " + record.msg
        return True

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addFilter(RootFilter())
stream_handler = logging.StreamHandler()
root_logger.addHandler(stream_handler)

child_logger = logging.getLogger(__name__)
child_logger.setLevel(logging.WARNING)
child_logger.addHandler(stream_handler)


root_logger.info("Hello World!")
