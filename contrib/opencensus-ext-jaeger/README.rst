OpenCensus Jaeger Exporter
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-jaeger.svg
   :target: https://pypi.org/project/opencensus-ext-jaeger/

Installation
------------

::

    pip install opencensus-ext-jaeger

Usage
-----

The **OpenCensus Jaeger Exporter** allows you to export `OpenCensus`_ traces to `Jaeger`_.

.. _Jaeger: https://www.jaegertracing.io/
.. _OpenCensus: https://github.com/census-instrumentation/opencensus-python/

.. code:: python

    from opencensus.ext.jaeger.trace_exporter import JaegerExporter
    from opencensus.trace import tracer as tracer_module

    tracer = tracer_module.Tracer(exporter=JaegerExporter(
        service_name='my service',
        agent_host_name='localhost',
        agent_port=6831,
    ))

    with tracer.span(name='hello'):
        print('Hello, World!')

References
----------

* `Jaeger <https://www.jaegertracing.io/>`_
* `OpenCensus Project <https://opencensus.io/>`_
