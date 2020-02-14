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

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    INSTRUMENTATION_KEY = '<your-ikey-here>'
    CONNECTION_STRING = 'connection_string="InstrumentationKey=' + \
        INSTRUMENTATION_KEY + '"'
    sampler = 'opencensus.trace.samplers.ProbabilitySampler(rate=1.0)'
    OPENCENSUS = {
        'TRACE': {
            'SAMPLER': sampler,
            'EXPORTER': 'opencensus.ext.azure.trace_exporter.AzureExporter('
            + CONNECTION_STRING + ')',
            'BLACKLIST_PATHS': ['blacklist'],
        }
    }
