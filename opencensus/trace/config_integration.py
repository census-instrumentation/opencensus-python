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

SUPPORTED_INTEGRATIONS = {
    'httplib': 'opencensus.trace.ext.httplib',
    'requests': 'opencensus.trace.ext.requests',
    'google_cloud_clientlibs': 'opencensus.trace.ext.google_cloud_clientlibs',
    'threading': 'opencensus.trace.ext.threading',

    'mysql': 'opencensus.ext.mysql',
    'postgresql': 'opencensus.ext.postgresql',
    'pymysql': 'opencensus.ext.pymysql',
    'sqlalchemy': 'opencensus.ext.sqlalchemy',
}


def trace_integrations(integrations, tracer=None):
    """Enable tracing on the selected integrations.

    :type integrations: list
    :param integrations: The integrations to be traced.
    """
    integrated = []

    for item in integrations:
        try:
            path_to_module = SUPPORTED_INTEGRATIONS[item]
            module = importlib.import_module(path_to_module)
            module.trace_integration(tracer=tracer)
            integrated.append(item)
        except Exception as e:
            log.warning(
                'Failed to integrate module: {}, supported integrations are {}'
                .format(
                    item,
                    ', '.join(str(x) for x in SUPPORTED_INTEGRATIONS)))
            log.warning('{}'.format(e))

    return integrated
