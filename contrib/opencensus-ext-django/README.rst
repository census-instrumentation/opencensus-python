OpenCensus Django Integration
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-django.svg
   :target: https://pypi.org/project/opencensus-ext-django/

Installation
------------

::

    pip install opencensus-ext-django

Usage
-----

For tracing Django requests, you will need to add the following line to
the ``MIDDLEWARE_CLASSES`` section in the Django ``settings.py`` file.

.. code:: python

    MIDDLEWARE_CLASSES = [
        ...
        'opencensus.ext.django.middleware.OpencensusMiddleware',
    ]

And add this line to the ``INSTALLED_APPS`` section:

.. code:: python

    INSTALLED_APPS = [
        ...
        'opencensus.ext.django',
    ]

You can configure the sampler, exporter, propagator using the ``OPENCENSUS_TRACE`` setting in
``settings.py``:

.. code:: python

    OPENCENSUS_TRACE = {
        'SAMPLER': 'opencensus.trace.samplers.probability.ProbabilitySampler',
        'REPORTER': 'opencensus.trace.print_exporter.PrintExporter',
        'PROPAGATOR': 'opencensus.trace.propagation.google_cloud_format.'
                      'GoogleCloudFormatPropagator',
    }

You can configure the sampling rate and other parameters using the ``OPENCENSUS_TRACE_PARAMS``
setting in ``settings.py``:

.. code:: python

    OPENCENSUS_TRACE_PARAMS = {
        'BLACKLIST_PATHS': ['/_ah/health'],
        'GCP_EXPORTER_PROJECT': None,
        'SAMPLING_RATE': 0.5,
        'SERVICE_NAME': 'my_service',
        'ZIPKIN_EXPORTER_HOST_NAME': 'localhost',
        'ZIPKIN_EXPORTER_PORT': 9411,
        'ZIPKIN_EXPORTER_PROTOCOL': 'http',
    }
