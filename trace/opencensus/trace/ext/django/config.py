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

from django.conf import settings as django_settings

DEFAULT_DJANGO_TRACER_CONFIG = {
    'SAMPLER': 'opencensus.trace.samplers.always_on.AlwaysOnSampler',
    'REPORTER': 'opencensus.trace.reporters.print_reporter.PrintReporter',
    'PROPAGATOR': 'opencensus.trace.propagation.google_cloud_format.'
                  'GoogleCloudFormatPropagator',
}

PATH_DELIMITER = '.'


class DjangoTraceSettings(object):
    """Set the params for a django tracer, including the tracer, sampler and
    reporter. If the user did not define the settings in django settings file.
    then use the dafaults.
    """

    def __init__(self):
        # Try to read the user settings from django settings file
        self.settings = getattr(
            django_settings,
            'OPENCENSUS_TRACE',
            DEFAULT_DJANGO_TRACER_CONFIG)

    def __getattr__(self, attr):
        # If not in defaults, it is something we cannot parse.
        if attr not in DEFAULT_DJANGO_TRACER_CONFIG:
            raise AttributeError('Attribute {} does not exist.'.format(attr))

        path = self.settings[attr]

        # Convert the string to import class
        module_class = convert_to_import(path)

        return module_class


def convert_to_import(path):
    """Given a string which represents the import path, convert to the
    class to import.
    """
    # Split the path string to module name and class name
    module_name, class_name = path.rsplit(PATH_DELIMITER, 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


settings = DjangoTraceSettings()
