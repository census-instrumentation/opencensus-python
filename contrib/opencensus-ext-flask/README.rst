OpenCensus Flask Integration
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-flask.svg
   :target: https://pypi.org/project/opencensus-ext-flask/

Installation
------------

::

    pip install opencensus-ext-flask

Usage
-----

.. code:: python

    from flask import Flask
    from opencensus.ext.flask.flask_middleware import FlaskMiddleware
    
    app = Flask(__name__)
    middleware = FlaskMiddleware(app, blacklist_paths=['_ah/health'])
    
    @app.route('/')
    def hello():
        return 'Hello World!'
    
    if __name__ == '__main__':
        import logging
        logger = logging.getLogger('werkzeug')
        logger.setLevel(logging.ERROR)
        app.run(host='localhost', port=8080, threaded=True)

Additional configuration can be provided, please read
`Customization <https://github.com/census-instrumentation/opencensus-python#customization>`_
for a complete reference.

.. code:: python

    app.config['OPENCENSUS'] = {
        'TRACE': {
            'SAMPLER': 'opencensus.trace.samplers.ProbabilitySampler(rate=1)',
            'EXPORTER': '''opencensus.ext.ocagent.trace_exporter.TraceExporter(
                service_name='foobar',
            )''',
        }
    }

References
----------

* `OpenCensus Project <https://opencensus.io/>`_
