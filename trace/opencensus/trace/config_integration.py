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

import importlib
import logging

log = logging.getLogger(__name__)

DEFAULT_INTEGRATIONS = {
    'mysql': True,
    'mongodb': False,
    'sqlite':False,
    'memcache': False,
    'elasticsearch': False,
    'redis':False,
}

PATH_PREFIX = 'opencensus.trace.ext'


def trace_integrations(integrations=None):
    """Enable tracing on the selected integrations.
    
    :type integrations: dict
    :param integrations: The integrations to be traced.
    """
    if integrations is None:
        integrations = DEFAULT_INTEGRATIONS

    for item in integrations.keys():
        if integrations.get(item):
            try:
                path_to_module = '{}.{}.trace'.format(PATH_PREFIX, item)
                module = importlib.import_module(path_to_module)
                module.trace()
            except Exception:
                log.debug(
                    'Failed to integrate module: {}'.format(item))
