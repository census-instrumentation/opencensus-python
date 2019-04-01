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

from multiprocessing.dummy import Pool as ThreadPool
import time
import threading
from opencensus.common.runtime_context import RuntimeContext

RuntimeContext.register_slot('operation_id', '<empty>')
_console_lock = threading.Lock()


def println(msg):
    with _console_lock:
        print(msg)


def work(name):
    println('Entering worker[{}]: {}'.format(name, RuntimeContext))
    RuntimeContext.operation_id = name
    time.sleep(0.01)
    println('Exiting worker[{}]: {}'.format(name, RuntimeContext))


if __name__ == "__main__":
    println('Main thread: {}'.format(RuntimeContext))
    RuntimeContext.operation_id = 'main'
    pool = ThreadPool(2)  # create a thread pool with 2 threads
    pool.map(RuntimeContext.with_current_context(work), [
        'bear',
        'cat',
        'dog',
        'horse',
        'rabbit',
    ])
    pool.close()
    pool.join()
    println('Main thread: {}'.format(RuntimeContext))
