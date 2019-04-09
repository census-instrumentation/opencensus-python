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

from flask import Flask
import requests

from opencensus.ext.azure.utils import Config
from opencensus.trace import config_integration
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.trace.propagation.trace_context_http_header_format \
    import TraceContextPropagator

app = Flask(__name__)
middleware = FlaskMiddleware(
    app,
    exporter=AzureExporter(config=Config(
        instrumentation_key='33018a74-404a-45ba-ba5d-079020eb7bba',
    )),
    propagator=TraceContextPropagator(),
)


@app.route('/')
def hello():
    requests.get('https://www.wikipedia.org/')
    return 'Hello World!'


if __name__ == '__main__':
    import logging
    logger = logging.getLogger('werkzeug')
    logger.setLevel(logging.ERROR)
    config_integration.trace_integrations(['requests'])
    app.run(host='localhost', port=8080, threaded=True)
