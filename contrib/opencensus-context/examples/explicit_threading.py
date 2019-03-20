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

from threading import Thread
from opencensus.common.runtime_context import RuntimeContext

RuntimeContext.register_slot('correlation_context', lambda: dict())


def withcc(fn):
    fork = RuntimeContext.correlation_context.copy()
    def callcc(*args, **kwargs):
        try:
            snapshot = RuntimeContext.correlation_context
            RuntimeContext.correlation_context = fork
            return fn(*args, **kwargs)
        finally:
            RuntimeContext.correlation_context = snapshot
    return callcc


def work(name):
    print(RuntimeContext)
    RuntimeContext.correlation_context['name'] = name
    print(RuntimeContext)


if __name__ == '__main__':
    print(RuntimeContext)
    RuntimeContext.correlation_context['test'] = True
    print(RuntimeContext)

    # by default context is not propagated to worker thread
    thread = Thread(target=work, args=('foo',))
    thread.start()
    thread.join()

    # user can propagate context explicitly (withcc = with current context)
    thread = Thread(target=withcc(work), args=('foo',))
    thread.start()
    thread.join()
