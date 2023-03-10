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

import threading

_INTEGRATIONS_BIT_MASK = 0
_INTEGRATIONS_LOCK = threading.Lock()


class _Integrations:
    NONE = 0
    DJANGO = 1
    FLASK = 2
    GOOGLE_CLOUD = 4
    HTTP_LIB = 8
    LOGGING = 16
    MYSQL = 32
    POSTGRESQL = 64
    PYMONGO = 128
    PYMYSQL = 256
    PYRAMID = 512
    REQUESTS = 1024
    SQLALCHEMY = 2056
    HTTPX = 4096
    FASTAPI = 8192


def get_integrations():
    return _INTEGRATIONS_BIT_MASK


def add_integration(integration):
    with _INTEGRATIONS_LOCK:
        global _INTEGRATIONS_BIT_MASK  # pylint: disable=global-statement
        _INTEGRATIONS_BIT_MASK |= integration


def remove_intregration(integration):
    with _INTEGRATIONS_LOCK:
        global _INTEGRATIONS_BIT_MASK  # pylint: disable=global-statement
        _INTEGRATIONS_BIT_MASK &= ~integration
