from flask import Flask

from opencensus.ext.datadog.traces import DatadogTraceExporter, Options
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.trace.samplers import AlwaysOnSampler

app = Flask(__name__)
middleware = FlaskMiddleware(app,
                             excludelist_paths=['/healthz'],
                             sampler=AlwaysOnSampler(),
                             exporter=DatadogTraceExporter(
                                 Options(service='python-export-test',
                                         global_tags={"stack": "example"})))


@app.route('/')
def hello():
    return 'Hello World!'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True)
