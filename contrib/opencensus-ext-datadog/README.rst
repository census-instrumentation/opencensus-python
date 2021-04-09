OpenCensus Datadog Exporter
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-datadog.svg
   :target: https://pypi.org/project/opencensus-ext-datadog/

Installation
------------

::

    pip install opencensus-ext-datadog

Usage
-----

Trace
~~~~~

The **Datadog Trace Exporter** allows you to export `OpenCensus`_ traces to `Datadog`_.

This example shows how to send a span "hello" to Datadog.

* Set up a `Datadog Agent <https://docs.datadoghq.com/agent/>`_ that is accessible to your app.
* Place the URL for the agent in the `trace_addr` of the configuration options.

 .. code:: python

    from opencensus.ext.datadog.traces import DatadogTraceExporter, Options
    from opencensus.trace.samplers import ProbabilitySampler
    from opencensus.trace.tracer import Tracer

    tracer = Tracer(
        exporter=DatadogTraceExporter(Options(service='app-name',trace_addr='my-datdog-agent:8126`)),
        sampler=ProbabilitySampler(1.0)
    )

    with tracer.span(name='hello'):
        print('Hello, World!')

OpenCensus also supports several `integrations <https://github.com/census-instrumentation/opencensus-python#integration>`_ which allows OpenCensus to integrate with third party libraries.

This example shows how to integrate with the `requests <https://2.python-requests.org/en/master/>`_ library.

* Set up a `Datadog Agent <https://docs.datadoghq.com/agent/>`_ that is accessible to your app.
* Place the URL for the agent in the `trace_addr` of the configuration options.

.. code:: python

    import requests

    from opencensus.ext.datadog.traces import DatadogTraceExporter, Options
    from opencensus.trace.samplers import ProbabilitySampler
    from opencensus.trace.tracer import Tracer

    config_integration.trace_integrations(['requests'])
    tracer = Tracer(
        exporter=DatadogTraceExporter(
            Options(
                service='app-name',
                trace_addr='my-datdog-agent:8126`
                )
        ),
        sampler=ProbabilitySampler(1.0),
    )
    with tracer.span(name='parent'):
        response = requests.get(url='https://www.wikipedia.org/wiki/Rabbit')


References
----------

* `Datadog <https://www.datadoghq.com/product/>`_
* `Examples <https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-datadog/examples>`_
* `OpenCensus Project <https://opencensus.io/>`_

.. _Datadog: https://www.datadoghq.com/product/
.. _OpenCensus: https://github.com/census-instrumentation/opencensus-python/
