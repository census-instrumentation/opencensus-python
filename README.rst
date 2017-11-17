OpenCensus - A stats collection and distributed tracing framework
=================================================================

    This is the open-source release of Census for Python. Census provides a
    framework to measure a server's resource usage and collect performance
    stats. This repository contains python related utilities and supporting
    software needed by Census.

|circleci|

-  `API Documentation`_

.. _API Documentation: http://opencensus.io/opencensus-python/trace/usage.html

Installation
------------

1. Install the opencensus-trace package using pip

::

    pip install opencensus-trace

2. Initialize a tracer to enable trace in your application

.. code:: python

    from opencensus.trace import request_tracer

    tracer = request_tracer.RequestTracer()

Usage
-----

There are two ways to trace your code blocks. One is using a ``with``
statement to wrap your code, and the trace span will end when exit the
``with`` statement. Another is explicitly start and finish the trace
span before and after your code block. Sample code for the two usages as
below:

Usage 1: ``with`` statement (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    from opencensus.trace import request_tracer

    # Initialize a tracer, by default using the `PrintExporter`
    tracer = request_tracer.RequestTracer()

    # Example for creating nested spans
    with tracer.span(name='span1') as span1:
        do_something_to_trace()
        with span1.span(name='span1_child1') as span1_child1:
            do_something_to_trace()
        with span1.span(name='span1_child2') as span1_child2:
            do_something_to_trace()
    with tracer.span(name='span2') as span2:
        do_something_to_trace()

    # The spans will be exported when exiting the with block.

Usage 2: Explicitly start and end spans
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    from opencensus.trace import request_tracer

    # Initialize a tracer, by default using the `PrintExporter`
    tracer = request_tracer.RequestTracer()
    tracer.start_trace()

    tracer.start_span(name='span1')
    do_something_to_trace()
    tracer.end_span()

Customization
-------------

Samplers
~~~~~~~~

You can specify different samplers when initializing a tracer, default
is using ``AlwaysOnSampler``, the other options are ``AlwaysOffSampler``
and ``ProbabilitySampler``

.. code:: python

    from opencensus.trace.samplers import probability
    from opencensus.trace import request_tracer

    # Sampling the requests at the rate equals 0.5
    sampler = probability.ProbabilitySampler(rate=0.5)
    tracer = request_tracer.RequestTracer(sampler=sampler)

Exporters
~~~~~~~~~

You can choose different exporters to send the traces to. Default is
printing the traces in JSON format. The rest options are sending to
logging, or write to a file. Will add exporters to report to different
trace backend later.

.. code:: python

    from opencensus.trace.exporters import file_exporter
    from opencensus.trace.tracer import context_tracer

    # Export the traces to a local file
    exporter = file_exporter.FileExporter(file_name='traces')
    tracer = context_tracer.ContextTracer(exporter=exporter)

Report to Stackdriver Trace:

.. code:: python

    from opencensus.trace.exporters import stackdriver_exporter
    from opencensus.trace import request_tracer

    exporter = stackdriver_exporter.StackdriverExporter(
        project_id='your_cloud_project')
    tracer = request_tracer.RequestTracer(exporter=exporter)

Propagators
~~~~~~~~~~~

You can specify the propagator type for serialize and deserialize the
SpanContext and headers. Currently support
``GoogleCloudFormatPropagator``, ``TextFormatPropagator``.

.. code:: python

    from opencensus.trace.propagation import google_cloud_format

    propagator = google_cloud_format.GoogleCloudFormatPropagator()

    # Deserialize
    span_context = propagator.from_header(header)

    # Serialize
    header = propagator.to_header(span_context)

Blacklist Paths
~~~~~~~~~~~~~~~

You can specify which paths you do not want to trace by configuring the
blacklist paths. By default the health check path in GAE Flex is not traced,
but you can turn it on in the setting.

Here is the sample code for configuring the blacklist:

For Flask:

.. code:: python

    from opencensus.trace.ext.flask.flask_middleware import FlaskMiddleware

    app = flask.Flask(__name__)

    blacklist_paths = ['_ah/health']
    middleware = FlaskMiddleware(app, blacklist_paths=blacklist_paths)

For Django:

Add this line in the OPENCENSUS_PARAMS:

::

    'BLACKLIST_PATHS': ['_ah/health',]

Framework Integration
---------------------

Opencensus supports integration with popular web frameworks including
Django, Flask and Webapp2. When the application receives a HTTP request,
the tracer will automatically generate a span context using the trace
information extracted from the request headers, and propagated to the
child spans. Below is the sample code snippets:

Flask
~~~~~

In your application, use the middleware to wrap your app and the
requests will be automatically traced.

.. code:: python

    from opencensus.trace.ext.flask.flask_middleware import FlaskMiddleware

    app = flask.Flask(__name__)

    # You can also specify the sampler, exporter, propagator in the middleware,
    # default is using `AlwaysOnSampler` as sampler, `PrintExporter` as exporter,
    # `GoogleCloudFormatPropagator` as propagator.
    middleware = FlaskMiddleware(app)

Django
~~~~~~

For tracing Django requests, you will need to add the following line to
the ``MIDDLEWARE_CLASSES`` section in the Django ``settings.py`` file.

::

    'opencensus.trace.ext.django.middleware.OpencensusMiddleware',

Add this line to the ``INSTALLED_APPS`` section:

::

    'opencensus.trace.ext.django',

Customize the sampler, exporter, propagator in the ``settings.py`` file:

::

    OPENCENSUS_TRACE = {
        'SAMPLER': 'opencensus.trace.samplers.probability.ProbabilitySampler',
        'REPORTER': 'opencensus.trace.exporters.print_exporter.PrintExporter',
        'PROPAGATOR': 'opencensus.trace.propagation.google_cloud_format.'
                      'GoogleCloudFormatPropagator',
    }

Configure the sampling rate and other params:

::

    OPENCENSUS_TRACE_PARAMS = {
        'BLACKLIST_PATHS': ['/_ah/health'],
        'GCP_EXPORTER_PROJECT': None,
        'SAMPLING_RATE': 0.5,
        'ZIPKIN_EXPORTER_SERVICE_NAME': 'my_service',
        'ZIPKIN_EXPORTER_HOST_NAME': 'localhost',
        'ZIPKIN_EXPORTER_PORT': 9411,

    }

Then the requests will be automatically traced.

Webapp2
~~~~~~~

.. code:: python

    from opencensus.trace.tracer import webapp2_tracer

    tracer = webapp2_tracer.WebApp2Tracer()

    with tracer.span(name='span1'):
        do_something_to_trace()

Service Integration
-------------------

Opencensus supports integration with various popular services (working in progress).
By default there is no integration, you need to specify which service(s) you
want to instrument. Usage for enabling MySQL instrumentation like below:

.. code:: python

    from opencensus.trace import config_integration
    from opencensus.trace import request_tracer

    import mysql.connector

    INTEGRATIONS = ['mysql', 'postgresql']

    config_integration.trace_integrations(INTEGRATIONS)

    tracer = request_tracer.RequestTracer()

    conn = mysql.connector.connect(user='user', password='password')
    cursor = conn.cursor()
    query = 'SELECT 2*3'
    cursor.execute(query)

MySQL
~~~~~

The integration with MySQL is based on the mysql-connector-python library,
github link is https://github.com/mysql/mysql-connector-python.

Run this command to install this package,

.. code:: bash

    pip install mysql-connector

PostgreSQL
~~~~~~~~~~

The integration with PostgreSQL is based on the psycopg2 library, which is the
most popular PostgreSQL python library based on the download data in PSF stats.

Run this command to install this package,

.. code:: bash

    pip install psycopg2

SQLAlchemy
~~~~~~~~~~

Note that if enabled tracing both SQLAlchemy and the database it connected,
the communication between SQLAlchemy and the database will also be traced.
To avoid the verbose spans, you can just trace SQLAlchemy.

Run this command to install the SQLAlchemy package,

.. code:: bash

    pip install sqlalchemy

Requests
~~~~~~~~

Supports tracing the requests methods including get, post, put, delete, head
and options. The request url and status code will be added to the span labels.

As most of the Google Cloud client libraries supports HTTP as the background
transport, to trace the client libraries requests, you can turn on the trace
integration with requests module.

.. code:: python

    import requests
    import uuid

    from opencensus.trace.config_integration import trace_integrations
    from opencensus.trace.request_tracer import RequestTracer

    from google.cloud import bigquery

    # Create a tracer
    tracer = RequestTracer()

    # Integrate with requests module
    trace_integrations(['requests'])

    # Run a query to trace
    query = 'SELECT * FROM sample_table'
    client = bigquery.Client()
    query_job = client.run_async_query(str(uuid.uuid4()), query)

    # Start the query job and wait it to complete
    query_job.begin()
    query_job.result()

Then you will get the request trace data from the start of executing the query
to the end.

Status
------

Currently under active development.

Development
-----------

Tests
~~~~~

::

    cd trace
    tox -e py34
    source .tox/py34/bin/activate

    # Run the unit test
    pip install nox-automation

    # See what's available in the nox suite
    nox -l

    # Run a single nox command
    nox -s "unit_tests(python_version='2.7')"

    # Run all the nox commands
    nox

    # Integration test
    # We don't have script for integration test yet, but can test as below.
    python setup.py bdist_wheel
    cd dist
    pip install opencensus-0.0.1-py2.py3-none-any.whl

    # Then just run the tracers normally as you want to test.

Contributing
------------

Contributions to this library are always welcome and highly encouraged.

See `CONTRIBUTING <CONTRIBUTING.md>`__ for more information on how to
get started.

License
-------

Apache 2.0 - See `LICENSE <LICENSE>`__ for more information.

Disclaimer
----------

This is not an official Google product.