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
    from opencensus.trace.propagation.trace_context_http_header_format import TraceContextPropagator
    
    app = Flask(__name__)
    middleware = FlaskMiddleware(app, propagator=TraceContextPropagator(), blacklist_paths=['_ah/health'])
    
    @app.route('/')
    def hello():
        return 'Hello World!'
    
    if __name__ == '__main__':
        import logging
        logger = logging.getLogger('werkzeug')
        logger.setLevel(logging.ERROR)
        app.run(host='localhost', port=8080, threaded=True)
