OpenCensus - A stats collection and distributed tracing framework
=================================================================

|gitter|
|circleci|
|pypi|

.. |circleci| image:: https://circleci.com/gh/census-instrumentation/opencensus-python.svg?style=shield
   :target: https://circleci.com/gh/census-instrumentation/opencensus-python
.. |gitter| image:: https://badges.gitter.im/census-instrumentation/lobby.svg
   :target: https://gitter.im/census-instrumentation/lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
.. |pypi| image:: https://badge.fury.io/py/opencensus.svg
   :target: https://pypi.org/project/opencensus/

`OpenCensus`_ for Python. OpenCensus provides a framework to measure a
server's resource usage and collect performance stats. This repository
contains Python related utilities and supporting software needed by
OpenCensus.

.. _OpenCensus: https://github.com/census-instrumentation

-  `API Documentation`_

.. _API Documentation: https://opencensus.io/api/python/trace/usage.html

--------
 Tracing
--------

Installation & basic usage
--------------------------

1. Install the opencensus package using `pip`_ or `pipenv`_:

    ::

        pip install opencensus
        pipenv install opencensus

2. Initialize a tracer for your application:

    .. code:: python

        from opencensus.trace import tracer as tracer_module

        tracer = tracer_module.Tracer()

    .. _pip: https://pip.pypa.io
    .. _pipenv: https://docs.pipenv.org/

3. Initialize a view_manager and a stats_recorder for your application:

    .. code:: python

        from opencensus.stats import stats as stats_module

        stats = stats_module.Stats()
        view_manager = stats.view_manager
        stats_recorder = stats.stats_recorder


Usage
-----

You can collect traces using the ``Tracer`` `context manager`_:

.. code:: python

    from opencensus.trace import tracer as tracer_module

    # Initialize a tracer, by default using the `PrintExporter`
    tracer = tracer_module.Tracer()

    # Example for creating nested spans
    with tracer.span(name='span1') as span1:
        do_something_to_trace()
        with span1.span(name='span1_child1') as span1_child1:
            do_something_to_trace()
        with span1.span(name='span1_child2') as span1_child2:
            do_something_to_trace()
    with tracer.span(name='span2') as span2:
        do_something_to_trace()

OpenCensus will collect everything within the ``with`` statement as a single span.

Alternatively, you can explicitly start and end a span:

.. code:: python

    from opencensus.trace import tracer as tracer_module

    # Initialize a tracer, by default using the `PrintExporter`
    tracer = tracer_module.Tracer()

    tracer.start_span(name='span1')
    do_something_to_trace()
    tracer.end_span()


.. _context manager: https://docs.python.org/3/reference/datamodel.html#context-managers


Customization
-------------

Samplers
~~~~~~~~

You can specify different samplers when initializing a tracer, default
is using ``AlwaysOnSampler``, the other options are ``AlwaysOffSampler``
and ``ProbabilitySampler``

.. code:: python

    from opencensus.trace.samplers import probability
    from opencensus.trace import tracer as tracer_module

    # Sampling the requests at the rate equals 0.5
    sampler = probability.ProbabilitySampler(rate=0.5)
    tracer = tracer_module.Tracer(sampler=sampler)

Exporters
~~~~~~~~~

By default, the traces are printed to stdout in JSON format. You can choose
different exporters to send the traces to. There are three built-in exporters,
which are ``opencensus.trace.print_exporter``, ``opencensus.trace.file_exporter``
and ``opencensus.trace.logging_exporter``, other exporters are provided as
`extensions <#trace-exporter>`__.

This example shows how to configure OpenCensus to save the traces to a
file:

.. code:: python

    from opencensus.trace import file_exporter
    from opencensus.trace.tracers import context_tracer

    exporter = file_exporter.FileExporter(file_name='traces')
    tracer = context_tracer.ContextTracer(exporter=exporter)

Propagators
~~~~~~~~~~~

You can specify the propagator type for serializing and deserializing the
``SpanContext`` and its headers. There are currently three built in propagators:
``GoogleCloudFormatPropagator``, ``TextFormatPropagator`` and ``TraceContextPropagator``.

This example shows how to use the ``GoogleCloudFormatPropagator``:

.. code:: python

    from opencensus.trace.propagation import google_cloud_format

    propagator = google_cloud_format.GoogleCloudFormatPropagator()

    # Deserialize
    span_context = propagator.from_header(header)

    # Serialize
    header = propagator.to_header(span_context)

This example shows how to use the ``TraceContextPropagator``:

.. code:: python

    import requests

    from opencensus.trace import config_integration
    from opencensus.trace.propagation.trace_context_http_header_format import TraceContextPropagator
    from opencensus.trace.tracer import Tracer

    config_integration.trace_integrations(['httplib'])
    tracer = Tracer(propagator=TraceContextPropagator())

    with tracer.span(name='parent'):
        with tracer.span(name='child'):
            response = requests.get('http://localhost:5000')

Blacklist Paths
~~~~~~~~~~~~~~~

You can specify which paths you do not want to trace by configuring the
blacklist paths.

This example shows how to configure the blacklist to ignore the ``_ah/health`` endpoint
for a Flask application:

.. code:: python

    from opencensus.trace.ext.flask.flask_middleware import FlaskMiddleware

    app = flask.Flask(__name__)

    blacklist_paths = ['_ah/health']
    middleware = FlaskMiddleware(app, blacklist_paths=blacklist_paths)

For Django, you can configure the blacklist in the ``OPENCENSUS_TRACE_PARAMS`` in ``settings.py``:

.. code:: python

    OPENCENSUS_TRACE_PARAMS: {
        ...
        'BLACKLIST_PATHS': ['_ah/health',],
    }


.. note:: By default, the health check path for the App Engine flexible environment is not traced,
    but you can turn it on by excluding it from the blacklist setting.

------------
 Extensions
------------

Integration
-----------

OpenCensus supports integration with popular web frameworks, client libraries and built-in libraries.

-  `Django`_
-  `Flask`_
-  `Google Cloud Client Libraries`_
-  `gRPC`_
-  `httplib`_
-  `MySQL`_
-  `PostgreSQL`_
-  `pymongo`_
-  `PyMySQL`_
-  `Pyramid`_
-  `requests`_
-  `SQLAlchemy`_
-  `threading`_

Trace Exporter
--------------

-  `Jaeger`_
-  `OCAgent`_
-  `Stackdriver`_
-  `Zipkin`_

Stats Exporter
--------------

-  `Prometheus`_
-  `Stackdriver`_

.. _Django: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-django
.. _Flask: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-flask
.. _Google Cloud Client Libraries: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-google-cloud-clientlibs
.. _gRPC: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-grpc
.. _httplib: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-httplib
.. _Jaeger: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-jaeger
.. _MySQL: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-mysql
.. _OCAgent: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-ocagent
.. _PostgreSQL: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-postgresql
.. _Prometheus: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-prometheus
.. _pymongo: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-pymongo
.. _PyMySQL: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-pymysql
.. _Pyramid: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-pyramid
.. _requests: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-requests
.. _SQLAlchemy: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-sqlalchemy
.. _Stackdriver: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-stackdriver
.. _threading: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-threading
.. _Zipkin: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-zipkin

------------------
 Additional Info
------------------

Contributing
------------

Contributions to this library are always welcome and highly encouraged.

See `CONTRIBUTING <CONTRIBUTING.md>`__ for more information on how to
get started.


Development
-----------

Tests
~~~~~

::

    cd trace
    tox -e py34
    source .tox/py34/bin/activate

    # Install nox with pip
    pip install nox-automation

    # See what's available in the nox suite
    nox -l

    # Run a single nox command
    nox -s "unit(py='2.7')"

    # Run all the nox commands
    nox

    # Integration test
    # We don't have script for integration test yet, but can test as below.
    python setup.py bdist_wheel
    cd dist
    pip install opencensus-0.0.1-py2.py3-none-any.whl

    # Then just run the tracers normally as you want to test.

License
-------

Apache 2.0 - See `LICENSE <LICENSE>`__ for more information.

Disclaimer
----------

This is not an official Google product.
