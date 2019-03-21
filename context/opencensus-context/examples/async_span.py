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

import asyncio
from opencensus.common.runtime_context import RuntimeContext

RuntimeContext.register_slot('current_span', None)


class Span(object):
    def __init__(self, name):
        self.name = name
        self.parent = RuntimeContext.current_span

    def __repr__(self):
        return ('{}(name={}, parent={})'
                .format(
                    type(self).__name__,
                    self.name,
                    self.parent,
                ))

    async def __aenter__(self):
        RuntimeContext.current_span = self

    async def __aexit__(self, exc_type, exc, tb):
        RuntimeContext.current_span = self.parent


async def main():
    print(RuntimeContext)
    async with Span('foo'):
        print(RuntimeContext)
        await asyncio.sleep(0.1)
        async with Span('bar'):
            print(RuntimeContext)
            await asyncio.sleep(0.1)
        print(RuntimeContext)
        await asyncio.sleep(0.1)
    print(RuntimeContext)


if __name__ == '__main__':
    asyncio.run(main())
