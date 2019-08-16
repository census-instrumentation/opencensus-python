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

import logging
import os
import sys

from opencensus.ext.azure.common.protocol import BaseObject

logger = logging.getLogger(__name__)

ENV_INSTRUMENTATION_KEY = 'APPINSIGHTS_INSTRUMENTATIONKEY'
ENV_CONNECTION_STRING = 'APPLICATIONINSIGHTS_CONNECTION_STRING'
INSTRUMENTATION_KEY = 'InstrumentationKey'
INGESTION_ENDPOINT = 'IngestionEndpoint'


def process_options(options):
    env_ikey = os.getenv(ENV_INSTRUMENTATION_KEY)
    env_cs = os.getenv(ENV_CONNECTION_STRING)
    code_ikey = options.instrumentation_key
    code_endpoint = options.endpoint
    options.instrumentation_key = None
    options.endpoint = None
    
    if options.connection_string is not None:
        # Hardcoded connection string
        cs = parse_connection_string(options.connection_string)
        ikey = cs.get(INSTRUMENTATION_KEY)
        if ikey is not None:
            options.instrumentation_key = ikey
        else:
            logger.warning('Missing \'InstrumentationKey\' in connection string')
        endpoint = cs.get(INGESTION_ENDPOINT)
        if endpoint is not None:
            options.endpoint = endpoint + '/v2/track'
    if options.instrumentation_key is None and code_ikey is not None:
        # Hardcoded instrumentation key
        options.instrumentation_key = code_ikey
    if options.instrumentation_key is None and env_cs is not None:
        # Environment variable connection string
        ikey = parse_connection_string(env_cs).get(INSTRUMENTATION_KEY)
        if ikey is not None:
            options.instrumentation_key = ikey
            return
        else:
            logger.warning('Missing \'InstrumentationKey\' in environment connection string')
        endpoint = cs.get(INGESTION_ENDPOINT)
        if endpoint is not None and options.endpoint is None:
            options.endpoint = endpoint + '/v2/track'
    # Environment variable instrumentation key
    if options.instrumentation_key is None:
        options.instrumentation_key = env_ikey
    if options.endpoint is None:
        options.endpoint = code_endpoint
        

def parse_connection_string(connection_string):
    try:
        pairs = connection_string.split(';')
        return dict(s.split('=') for s in pairs)
    except Exception:
        raise ValueError("Invalid connection string: " + connection_string)


class Options(BaseObject):
    def __init__(self, *args, **kwargs):
        super(Options, self).__init__(*args, **kwargs)
        process_options(self)

    _default = BaseObject(
        connection_string=None,
        enable_standard_metrics=False,
        endpoint='https://dc.services.visualstudio.com/v2/track',
        export_interval=15.0,
        grace_period=5.0,
        instrumentation_key=None,
        max_batch_size=100,
        minimum_retry_interval=60,  # minimum retry interval in seconds
        proxy=None,
        storage_maintenance_period=60,
        storage_max_size=100*1024*1024,
        storage_path=os.path.join(
            os.path.expanduser('~'),
            '.opencensus',
            '.azure',
            os.path.basename(sys.argv[0]) or '.console',
        ),
        storage_retention_period=7*24*60*60,
        timeout=10.0,  # networking timeout in seconds
    )
