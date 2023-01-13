# Copyright 2020, OpenCensus Authors
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

import os
import threading

_STATSBEAT_STATE = {
    "INITIAL_FAILURE_COUNT": 0,
    "INITIAL_SUCCESS": False,
    "SHUTDOWN": False,
}
_STATSBEAT_STATE_LOCK = threading.Lock()


def is_statsbeat_enabled():
    disabled = os.environ.get("APPLICATIONINSIGHTS_STATSBEAT_DISABLED_ALL")
    return disabled is None or disabled.lower() != "true"


def increment_statsbeat_initial_failure_count():
    with _STATSBEAT_STATE_LOCK:
        _STATSBEAT_STATE["INITIAL_FAILURE_COUNT"] += 1


def get_statsbeat_initial_failure_count():
    return _STATSBEAT_STATE["INITIAL_FAILURE_COUNT"]


def set_statsbeat_initial_success(success):
    with _STATSBEAT_STATE_LOCK:
        _STATSBEAT_STATE["INITIAL_SUCCESS"] = success


def get_statsbeat_initial_success():
    return _STATSBEAT_STATE["INITIAL_SUCCESS"]


def get_statsbeat_shutdown():
    return _STATSBEAT_STATE["SHUTDOWN"]
