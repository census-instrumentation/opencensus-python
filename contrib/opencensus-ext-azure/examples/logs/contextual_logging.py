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

from opencensus.ext.azure.log_exporter import AzureLogHandler

logger = logging.getLogger(__name__)
# TODO: you need to specify the instrumentation key in a connection string
# and place it in the APPLICATIONINSIGHTS_CONNECTION_STRING
# environment variable.
logger.addHandler(AzureLogHandler())

# For more details on contextual logging patterns in python, see:
# https://docs.python.org/3/howto/logging-cookbook.html#adding-contextual-information-to-your-logging-output

'''
Option 1: Use LoggerAdapters to add custom dimensions
'''


class CustomDimensionsAdapter(logging.LoggerAdapter):

    @property
    def custom_dimensions(self):
        if self.extra and 'custom_dimensions' in self.extra:
            return self.extra['custom_dimensions']
        else:
            return {}

    def process(self, msg, kwargs):

        if self.custom_dimensions:
            if 'extra' not in kwargs:
                kwargs['extra'] = {'custom_dimensions': self.custom_dimensions}

            elif 'extra' in kwargs and 'custom_dimensions' in kwargs['extra']:
                kwargs['extra'] = {
                    'custom_dimensions': {
                        **self.custom_dimensions,
                        **kwargs['extra']['custom_dimensions']
                    }
                }

        return msg, kwargs


adapter = CustomDimensionsAdapter(logger, extra={
    'custom_dimensions': {
        'contextual_key': 'contextual_value'
    }})

adapter.warning('message_with_adapter')
adapter.warning('message_with_adapter', extra={
    'custom_dimensions': {
        'optional_extra_key': 'optional_extra_value'
    }})
adapter.warning('message_with_adapter_%s', 'arg', extra={
    'custom_dimensions': {
        'optional_extra_key': 'optional_extra_value'
    }})

'''
Option 2: Use Logging Filters to add custom dimensions
'''


class CustomDimensionsFilter(logging.Filter):

    def __init__(self, custom_dimensions: dict, *args, **kwargs):
        super(CustomDimensionsFilter, self).__init__(*args, **kwargs)
        self.custom_dimensions = custom_dimensions

    def filter(self, record):

        if hasattr(record, 'custom_dimensions'):
            record.custom_dimensions.update(self.custom_dimensions)
        else:
            setattr(record, 'custom_dimensions', self.custom_dimensions)

        return True


f = CustomDimensionsFilter(custom_dimensions={
    'contextual_key': 'contextual_value'
    })
logger.addFilter(f)

logger.warning('message_with_filter')
logger.warning('message_with_filter', extra={
    'custom_dimensions': {
        'optional_extra_key': 'optional_extra_value'
    }})
logger.warning('message_with_filter_%s', 'arg', extra={
    'custom_dimensions': {
        'optional_extra_key': 'optional_extra_value'
    }})
