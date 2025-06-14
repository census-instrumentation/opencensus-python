   **Warning**

   OpenCensus and OpenTracing have merged to form
   `OpenTelemetry <https://opentelemetry.io>`__, which serves as the
   next major version of OpenCensus and OpenTracing.

   OpenTelemetry has now reached feature parity with OpenCensus, with
   tracing and metrics SDKs available in .NET, Golang, Java, NodeJS, and
   Python. **All OpenCensus Github repositories will be archived**. We
   encourage users to migrate to OpenTelemetry.

   To help you gradually migrate your instrumentation to OpenTelemetry,
   bridges are available in Java, Go, Python (tracing only), and JS. `Read the
   full blog post to learn more
   <https://opentelemetry.io/blog/2023/sunsetting-opencensus/>`__.

OpenCensus - A stats collection and distributed tracing framework
=================================================================

|gitter|
|travisci|
|circleci|
|pypi|
|compat_check_pypi|
|compat_check_github|


.. |travisci| image:: https://travis-ci.org/census-instrumentation/opencensus-python.svg?branch=master
    :target: https://travis-ci.org/census-instrumentation/opencensus-python
.. |circleci| image:: https://circleci.com/gh/census-instrumentation/opencensus-python.svg?style=shield
   :target: https://circleci.com/gh/census-instrumentation/opencensus-python
.. |gitter| image:: https://badges.gitter.im/census-instrumentation/lobby.svg
   :target: https://gitter.im/census-instrumentation/lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
.. |pypi| image:: https://badge.fury.io/py/opencensus.svg
   :target: https://pypi.org/project/opencensus/
.. |compat_check_pypi| image:: https://python-compatibility-tools.appspot.com/one_badge_image?package=opencensus
   :target: https://python-compatibility-tools.appspot.com/one_badge_target?package=opencensus
.. |compat_check_github| image:: https://python-compatibility-tools.appspot.com/one_badge_image?package=git%2Bgit%3A//github.com/census-instrumentation/opencensus-python.git
   :target: https://python-compatibility-tools.appspot.com/one_badge_target?package=git%2Bgit%3A//github.com/census-instrumentation/opencensus-python.git

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

        from opencensus.trace.tracer import Tracer
        from opencensus.trace.samplers import AlwaysOnSampler

        tracer = Tracer(sampler=AlwaysOnSampler())

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

    from opencensus.trace.tracer import Tracer
    from opencensus.trace.samplers import AlwaysOnSampler

    # Initialize a tracer, by default using the `PrintExporter`
    tracer = Tracer(sampler=AlwaysOnSampler())

    # Example for creating nested spans
    with tracer.span(name='span1'):
        do_something_to_trace()
        with tracer.span(name='span1_child1'):
            do_something_to_trace()
        with tracer.span(name='span1_child2'):
            do_something_to_trace()
    with tracer.span(name='span2'):
        do_something_to_trace()

OpenCensus will collect everything within the ``with`` statement as a single span.

Alternatively, you can explicitly start and end a span:

.. code:: python

    from opencensus.trace.tracer import Tracer
    from opencensus.trace.samplers import AlwaysOnSampler

    # Initialize a tracer, by default using the `PrintExporter`
    tracer = Tracer(sampler=AlwaysOnSampler())

    tracer.start_span(name='span1')
    do_something_to_trace()
    tracer.end_span()


.. _context manager: https://docs.python.org/3/reference/datamodel.html#context-managers


Customization
-------------

There are several things you can customize in OpenCensus:

* **Excludelist**, which excludes certain hosts and paths from being tracked.
  By default, the health check path for the App Engine flexible environment is
  not tracked, you can turn it on by excluding it from the excludelist setting.

* **Exporter**, which sends the traces.
  By default, the traces are printed to stdout in JSON format. You can choose
  different exporters to send the traces to. There are three built-in exporters,
  which are ``PrintExporter``, ``FileExporter`` and ``LoggingExporter``, the
  other exporters are provided as `extensions <#trace-exporter>`__.

* **Sampler**, which determines how traces are sampled.
  The default sampler is the ``ProbabilitySampler``, which samples (i.e.
  enables tracing for) a percentage of all requests. Sampling is deterministic
  according to the trace ID. To force sampling for all requests, or to prevent
  any request from being sampled, see ``AlwaysOnSampler`` and
  ``AlwaysOffSampler``.

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
    from opencensus.trace.samplers import ProbabilitySampler

    config_integration.trace_integrations(['httplib'])

    tracer = tracer_module.Tracer(
        exporter=file_exporter.FileExporter(file_name='traces'),
        propagator=google_cloud_format.GoogleCloudFormatPropagator(),
        sampler=ProbabilitySampler(rate=0.5),
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
            'EXCLUDELIST_HOSTNAMES': ['localhost', '127.0.0.1'],
            'EXCLUDELIST_PATHS': ['_ah/health'],
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
-  `gevent`_
-  `Google Cloud Client Libraries`_
-  `gRPC`_
-  `httplib`_
-  `httpx`_
-  `logging`_
-  `MySQL`_
-  `PostgreSQL`_
-  `pymongo`_
-  `PyMySQL`_
-  `Pyramid`_
-  `requests`_
-  `SQLAlchemy`_
-  `threading`_

Log Exporter
------------

-  `Azure`_

Metrics Exporter
----------------

-  `Azure`_

Stats Exporter
--------------

-  `OCAgent`_
-  `Prometheus`_
-  `Stackdriver`_

Trace Exporter
--------------

-  `Azure`_
-  `Datadog`_
-  `Jaeger`_
-  `OCAgent`_
-  `Stackdriver`_
-  `Zipkin`_

.. _Azure: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-azure
.. _Datadog: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-datadog
.. _Django: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-django
.. _Flask: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-flask
.. _FastAPI: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-fastapi
.. _gevent: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-gevent
.. _Google Cloud Client Libraries: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-google-cloud-clientlibs
.. _gRPC: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-grpc
.. _httplib: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-httplib
.. _httpx: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-httpx 
.. _Jaeger: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-jaeger
.. _logging: https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-logging
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

------------
 Versioning
------------

This library follows `Semantic Versioning`_.

**GA**: Libraries defined at a GA quality level are stable, and will not introduce
backwards-incompatible changes in any minor or patch releases. We will address issues and requests
with the highest priority. If we were to make a backwards-incompatible changes on an API, we will
first mark the existing API as deprecated and keep it for 18 months before removing it.

**Beta**: Libraries defined at a Beta quality level are expected to be mostly stable and we're
working towards their release candidate. We will address issues and requests with a higher priority.
There may be backwards incompatible changes in a minor version release, though not in a patch
release. If an element is part of an API that is only meant to be used by exporters or other
opencensus libraries, then there is no deprecation period. Otherwise, we will deprecate it for 18
months before removing it, if possible.

.. _Semantic Versioning: https://semver.org/
