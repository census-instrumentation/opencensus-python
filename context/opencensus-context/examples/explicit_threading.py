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

RuntimeContext.register_slot('operation_id', '<empty>')


def work(name):
    print('Entering worker:', RuntimeContext)
    RuntimeContext.operation_id = name
    print('Exiting worker:', RuntimeContext)


if __name__ == '__main__':
    print('Main thread:', RuntimeContext)
    RuntimeContext.operation_id = 'main'

    print('Main thread:', RuntimeContext)

    # by default context is not propagated to worker thread
    thread = Thread(target=work, args=('foo',))
    thread.start()
    thread.join()

    print('Main thread:', RuntimeContext)

    # user can propagate context explicitly
    thread = Thread(
        target=RuntimeContext.with_current_context(work),
        args=('bar',),
    )
    thread.start()
    thread.join()

    print('Main thread:', RuntimeContext)
