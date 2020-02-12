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

from config import Config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from opencensus.trace import config_integration
from opencensus.ext.azure import metrics_exporter
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.flask.flask_middleware import FlaskMiddleware

logger = logging.getLogger(__name__)
app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

# Trace integrations for requests library and sqlalchemy sending queries to the
# underlying database
config_integration.trace_integrations(['requests'])
config_integration.trace_integrations(['sqlalchemy'])

# FlaskMiddleware will track requests for the Flask application and send
# request/dependency telemetry to Azure Monitor
middleware = FlaskMiddleware(app)

# Exporter for metrics, will send metrics data
exporter = metrics_exporter.new_metrics_exporter(
    enable_standard_metrics=False,
    connection_string='InstrumentationKey=' + Config.INSTRUMENTATION_KEY)

# Exporter for logs, will send logging data
logger.addHandler(AzureLogHandler(connection_string='InstrumentationKey=' + Config.INSTRUMENTATION_KEY))

from app import routes

if __name__ == '__main__':
    app.run(host='localhost', port=5000, threaded=True)
