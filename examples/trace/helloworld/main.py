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

import time

from opencensus.trace import execution_context
from opencensus.trace import print_exporter
from opencensus.trace.tracer import Tracer
from opencensus.trace.samplers import always_on


def function_to_trace():
    time.sleep(1)


def main():
    sampler = always_on.AlwaysOnSampler()
    exporter = print_exporter.PrintExporter()
    tracer = Tracer(sampler=sampler, exporter=exporter)

    with tracer.span(name='root'):
        tracer.add_attribute_to_current_span(
            attribute_key='example key', attribute_value='example value')
        function_to_trace()
        with tracer.span(name='child'):
            function_to_trace()

    # Get the current tracer
    tracer = execution_context.get_opencensus_tracer()

    # Explicitly create spans
    tracer.start_span()

    # Get current span
    execution_context.get_current_span()

    # Explicitly end span
    tracer.end_span()


if __name__ == '__main__':
    main()
