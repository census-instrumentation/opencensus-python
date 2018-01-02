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

from django.conf import settings as django_settings

DEFAULT_DJANGO_TRACER_CONFIG = {
    'SAMPLER': 'opencensus.trace.samplers.always_on.AlwaysOnSampler',
    'EXPORTER':
        'opencensus.trace.exporters.print_exporter.PrintExporter',
    'PROPAGATOR': 'opencensus.trace.propagation.google_cloud_format.'
                  'GoogleCloudFormatPropagator',
}

DEFAULT_DJANGO_TRACER_PARAMS = {
    # https://cloud.google.com/appengine/docs/flexible/python/
    # how-instances-are-managed#health_checking
    'BLACKLIST_PATHS': ['_ah/health'],
    'GCP_EXPORTER_PROJECT': None,
    'SAMPLING_RATE': 0.5,
    'ZIPKIN_EXPORTER_SERVICE_NAME': 'my_service',
    'ZIPKIN_EXPORTER_HOST_NAME': 'localhost',
    'ZIPKIN_EXPORTER_PORT': 9411,
    'TRANSPORT': 'opencensus.trace.exporters.transports.sync.SyncTransport',
}


PATH_DELIMITER = '.'
TRANSPORT = 'TRANSPORT'

log = logging.getLogger(__name__)


class DjangoTraceSettings(object):
    """Set the params for a django tracer, including the tracer, sampler and
    exporter. If the user did not define the settings in django settings file.
    then use the dafaults.
    """

    def __init__(self):
        # Try to read the user settings from django settings file
        self.settings = getattr(
            django_settings,
            'OPENCENSUS_TRACE',
            DEFAULT_DJANGO_TRACER_CONFIG)

        self.params = getattr(
            django_settings,
            'OPENCENSUS_TRACE_PARAMS',
            DEFAULT_DJANGO_TRACER_PARAMS)

        # Set default value for the tracer config if user not specified
        _set_default_configs(self.settings, DEFAULT_DJANGO_TRACER_CONFIG)

        # Set default value for the params if user not specified
        _set_default_configs(self.params, DEFAULT_DJANGO_TRACER_PARAMS)

    def __getattr__(self, attr):
        # If not in defaults, it is something we cannot parse.
        if attr not in DEFAULT_DJANGO_TRACER_CONFIG:
            raise AttributeError('Attribute {} does not exist.'.format(attr))

        path = self.settings[attr]

        # Convert the string to import class
        module_class = convert_to_import(path)

        return module_class


def _set_default_configs(user_settings, default):
    """Set the default value to user settings if user not specified
    the value.
    """
    for key in default:
        if key not in user_settings:
            user_settings[key] = default[key]

    return user_settings


def convert_to_import(path):
    """Given a string which represents the import path, convert to the
    class to import.
    """
    # Split the path string to module name and class name
    try:
        module_name, class_name = path.rsplit(PATH_DELIMITER, 1)
        module = importlib.import_module(module_name)
        return getattr(module, class_name)
    except (ImportError, AttributeError):
        msg = 'Failed to import {}'.format(path)
        log.error(msg)

        raise ImportError(msg)


settings = DjangoTraceSettings()
