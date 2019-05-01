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

from wsgiref.simple_server import make_server

from opencensus.trace import config_integration
from opencensus.trace import print_exporter
from opencensus.trace import samplers

from app import main


config_integration.trace_integrations(['requests'])


def run_app():
    settings = {
        'OPENCENSUS': {
            'TRACE': {
                'EXPORTER': print_exporter.PrintExporter(),
                'SAMPLER': samplers.ProbabilitySampler(rate=1),
            }
        }
    }

    app = main({}, **settings)
    server = make_server('localhost', 8080, app)
    server.serve_forever()


if __name__ == '__main__':
    run_app()
