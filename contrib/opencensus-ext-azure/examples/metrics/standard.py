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

import psutil
import time

from opencensus.ext.azure import metrics_exporter


def main():
    # All you need is the next line. You can disable standard metrics by
    # passing in enable_standard_metrics=False into the constructor of
    # new_metrics_exporter()
    _exporter = metrics_exporter.new_metrics_exporter()

    print(_exporter.max_batch_size)
    for i in range(100):
        print(psutil.virtual_memory())
        time.sleep(5)

    print("Done recording metrics")


if __name__ == "__main__":
    main()
