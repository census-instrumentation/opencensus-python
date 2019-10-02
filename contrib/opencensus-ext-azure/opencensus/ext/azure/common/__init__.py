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

import os
import re
import sys

from opencensus.ext.azure.common.protocol import BaseObject

INGESTION_ENDPOINT = 'ingestionendpoint'
INSTRUMENTATION_KEY = 'instrumentationkey'


def process_options(options):
    code_cs = parse_connection_string(options.connection_string)
    code_ikey = options.instrumentation_key
    env_cs = parse_connection_string(
        os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING'))
    env_ikey = os.getenv('APPINSIGHTS_INSTRUMENTATIONKEY')

    # The priority of which value takes on the instrumentation key is:
    # 1. Key from explicitly passed in connection string
    # 2. Key from explicitly passed in instrumentation key
    # 3. Key from connection string in environment variable
    # 4. Key from instrumentation key in environment variable
    options.instrumentation_key = code_cs.get(INSTRUMENTATION_KEY) \
        or code_ikey \
        or env_cs.get(INSTRUMENTATION_KEY) \
        or env_ikey
    # The priority of the ingestion endpoint is as follows:
    # 1. The endpoint explicitly passed in connection string
    # 2. The endpoint from the connection string in environment variable
    # 3. The default breeze endpoint
    endpoint = code_cs.get(INGESTION_ENDPOINT) \
        or env_cs.get(INGESTION_ENDPOINT) \
        or 'https://dc.services.visualstudio.com'
    options.endpoint = endpoint + '/v2/track'


def parse_connection_string(connection_string):
    if connection_string is None:
        return {}
    try:
        pairs = connection_string.split(';')
        result = dict(s.split('=') for s in pairs)
        # Convert keys to lower-case due to case type-insensitive checking
        result = {key.lower(): value for key, value in result.items()}
    except Exception:
        raise ValueError('Invalid connection string')
    # Validate authorization
    auth = result.get('authorization')
    if auth is not None and auth.lower() != 'ikey':
        raise ValueError('Invalid authorization mechanism')
    # Construct the ingestion endpoint if not passed in explicitly
    if result.get(INGESTION_ENDPOINT) is None:
        endpoint_suffix = ''
        location_prefix = ''
        suffix = result.get('endpointsuffix')
        if suffix is not None:
            endpoint_suffix = suffix
            # Get regional information if provided
            prefix = result.get('location')
            if prefix is not None:
                location_prefix = prefix + '.'
            endpoint = 'https://' + location_prefix + 'dc.' + endpoint_suffix
            result[INGESTION_ENDPOINT] = endpoint
        else:
            # Default to None if cannot construct
            result[INGESTION_ENDPOINT] = None
    return result


class Options(BaseObject):
    def __init__(self, *args, **kwargs):
        super(Options, self).__init__(*args, **kwargs)
        process_options(self)

    _default = BaseObject(
        connection_string=None,
        enable_standard_metrics=True,
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


def validate_key(instrumentation_key):
    if not instrumentation_key:
        raise ValueError("Instrumentation key cannot be none or empty.")
    # Validate UUID format
    # Specs taken from https://tools.ietf.org/html/rfc4122
    pattern = re.compile('[0-9a-f]{8}-'
                         '[0-9a-f]{4}-'
                         '[1-5][0-9a-f]{3}-'
                         '[89ab][0-9a-f]{3}-'
                         '[0-9a-f]{12}')
    # re.fullmatch not available for python2
    # We use re.match, we matches from the beginning, and then do a length
    # check to ignore everything afterward.
    match = pattern.match(instrumentation_key)
    if len(instrumentation_key) != 36 or not match:
        raise ValueError("Invalid instrumentation key.")
