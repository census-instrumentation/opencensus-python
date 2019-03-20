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

from opencensus.common.runtime_context import RuntimeContext

RuntimeContext.register_slot('current_span', None)


class Span(object):
    def __init__(self, name):
        self.name = name
        self.parent = RuntimeContext.current_span

    def __repr__(self):
        return ('{}({})'.format(type(self).__name__, self.name))

    def __enter__(self):
        RuntimeContext.current_span = self

    def __exit__(self, type, value, traceback):
        RuntimeContext.current_span = self.parent

    def start(self):
        RuntimeContext.current_span = self

    def end(self):
        RuntimeContext.current_span = self.parent


if __name__ == '__main__':
    print(RuntimeContext)
    with Span('foo'):
        print(RuntimeContext)
        with Span('bar'):
            print(RuntimeContext)
        print(RuntimeContext)
    print(RuntimeContext)

    # explicit start/end span
    span = Span('baz')
    print(RuntimeContext)
    span.start()
    print(RuntimeContext)
    span.end()
    print(RuntimeContext)
