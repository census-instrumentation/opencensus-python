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
    exporter = metrics_exporter.new_metrics_exporter(export_interval=15.0, instrumentation_key='70c241c9-206e-4811-82b4-2bc8a52170b9')
    for i in range(100):
        print(psutil.virtual_memory())
        time.sleep(5)

    print("Done recording metrics")


if __name__ == "__main__":
    main()
