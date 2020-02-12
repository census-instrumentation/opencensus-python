from config import Config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from opencensus.trace import config_integration
from opencensus.ext.azure import metrics_exporter
from opencensus.ext.flask.flask_middleware import FlaskMiddleware

app = Flask(__name__)
app.config.from_object(Config)

middleware = FlaskMiddleware(app)
config_integration.trace_integrations(['requests'])
config_integration.trace_integrations(['sqlalchemy'])
db = SQLAlchemy(app)
exporter = metrics_exporter.new_metrics_exporter(
    enable_standard_metrics=False,
    connection_string='InstrumentationKey=70c241c9-206e-4811-82b4-2bc8a52170b9')

from app import routes

if __name__ == '__main__':
    app.run(host='localhost', port=5000, threaded=True)
