OpenCensus Celery Integration
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-celery.svg
   :target: https://pypi.org/project/opencensus-ext-celery/

Celery integration for OpenCensus provides the implementation of interceptors
for both the publisher side and consumer side to instrument the Celery tasks before
publishing and before and after consuming to get a result of the task.

Installation
------------

::

    pip install opencensus-ext-celery

Usage
-----

.. code:: python

    from opencensus.trace.propagation import trace_context_http_header_format
    from opencensus.trace import config_integration, samplers, print_exporter
    from opencensus.trace import tracer as tracer_module


    tracer = tracer_module.Tracer(
        sampler=samplers.ProbabilitySampler(),
        exporter=(print_exporter.PrintExporter()),
        propagator=trace_context_http_header_format.TraceContextPropagator())

    config_integration.trace_integrations(['celery'], tracer=tracer)

References
----------

* `OpenCensus Project <https://opencensus.io/>`_
* `Celery Project <http://www.celeryproject.org/>`_
