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
the ``MIDDLEWARE`` section in the Django ``settings.py`` file.

.. code:: python

    MIDDLEWARE = [
        ...
        'opencensus.ext.django.middleware.OpencensusMiddleware',
    ]

And add the ``OPENCENSUS`` section:

.. code:: python

    OPENCENSUS = {
        'TRACE': {
            'SAMPLER': 'opencensus.trace.samplers.ProbabilitySampler(rate=1)',
            'EXPORTER': '''opencensus.ext.ocagent.trace_exporter.TraceExporter(
                service_name='foobar',
            )''',
        }
    }
    
Additional configuration can be provided, please read
`Customization <https://github.com/census-instrumentation/opencensus-python#customization>`_
for a complete reference.

For customization the exporter has to be instantiated separately

.. code:: python

    from opencensus.ext.azure.trace_exporter import AzureExporter
    exporter = AzureExporter(service_name='mysite')
    exporter.add_telemetry_processor(callback)

    OPENCENSUS = {
        'TRACE': {
            'SAMPLER': 'opencensus.trace.samplers.ProbabilitySampler(rate=1)',
            'EXPORTER': exporter
        }
    }
    
    def callback(envelope):
    return False

Both forms assumes Environmental Variable ``APPINSIGHTS_INSTRUMENTATIONKEY`` exists.

References
----------

* `OpenCensus Project <https://opencensus.io/>`_
