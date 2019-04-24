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

        stats = stats_module.stats
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

There are several things you can customize in OpenCensus:

* **Blacklist**, which excludes certain hosts and paths from being tracked.
  By default, the health check path for the App Engine flexible environment is
  not tracked, you can turn it on by excluding it from the blacklist setting.

* **Exporter**, which sends the traces.
  By default, the traces are printed to stdout in JSON format. You can choose
  different exporters to send the traces to. There are three built-in exporters,
  which are ``PrintExporter``, ``FileExporter`` and ``LoggingExporter``, the
  other exporters are provided as `extensions <#trace-exporter>`__.

* **Sampler**, which determines how traces are sampled.
  The default sampler is ``AlwaysOnSampler``, other samplers include the
  ``AlwaysOffSampler`` and ``ProbabilitySampler``.

* **Propagator**, which serializes and deserializes the
  ``SpanContext`` and its headers. The default propagator is
  ``TraceContextPropagator``, other propagators include
  ``BinaryFormatPropagator``, ``GoogleCloudFormatPropagator`` and
  ``TextFormatPropagator``.


You can customize while initializing a tracer.

.. code:: python

    import requests

    from opencensus.trace import config_integration
    from opencensus.trace import file_exporter
    from opencensus.trace import tracer as tracer_module
    from opencensus.trace.propagation import google_cloud_format
    from opencensus.trace.samplers import probability

    config_integration.trace_integrations(['httplib'])

    tracer = tracer_module.Tracer(
        exporter=file_exporter.FileExporter(file_name='traces'),
        propagator=google_cloud_format.GoogleCloudFormatPropagator(),
        sampler=probability.ProbabilitySampler(rate=0.5),
    )

    with tracer.span(name='parent'):
        with tracer.span(name='child'):
            response = requests.get('http://localhost:5000')

You can use a configuration file for Flask/Django/Pyramid. For more
information, please read the
`individual integration documentation <#integration>`_.

.. code:: python

    'OPENCENSUS': {
        'TRACE': {
            'BLACKLIST_HOSTNAMES': ['localhost', '127.0.0.1'],
            'BLACKLIST_PATHS': ['_ah/health'],
            'SAMPLER': 'opencensus.trace.samplers.ProbabilitySampler(rate=1)',
            'EXPORTER': '''opencensus.ext.ocagent.trace_exporter.TraceExporter(
                service_name='foobar',
            )''',
            'PROPAGATOR': 'opencensus.trace.propagation.google_cloud_format.GoogleCloudFormatPropagator()',
        }
    }

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

-  `Azure`_
-  `Jaeger`_
-  `OCAgent`_
-  `Stackdriver`_
-  `Zipkin`_

Stats Exporter
--------------

-  `OCAgent`_
-  `Prometheus`_
-  `Stackdriver`_

.. _Azure: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-azure
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
