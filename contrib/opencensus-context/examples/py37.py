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

RuntimeContext.register_slot('correlation_context', lambda: dict())


async def hello(name):
    correlation_context = RuntimeContext.correlation_context.copy()
    correlation_context['name'] = name
    RuntimeContext.correlation_context = correlation_context

    for i in range(3):
        print('Hello {} {} {}'.format(
            name,
            i,
            RuntimeContext,
        ))
        await asyncio.sleep(0.1)


async def main():
    print(RuntimeContext)
    RuntimeContext.correlation_context['test'] = True
    print(RuntimeContext)
    await asyncio.gather(
        hello('foo'),
        hello('bar'),
        hello('baz'),
    )
    print(RuntimeContext)
    RuntimeContext.clear()
    print(RuntimeContext)


if __name__ == '__main__':
    asyncio.run(main())
