OpenCensus Zipkin Exporter
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-zipkin.svg
   :target: https://pypi.org/project/opencensus-ext-zipkin/

Installation
------------

::

    pip install opencensus-ext-zipkin

Usage
-----

The **OpenCensus Zipkin Exporter** allows you to export `OpenCensus`_ traces to `Zipkin`_.

.. _OpenCensus: https://github.com/census-instrumentation/opencensus-python/
.. _Zipkin: https://zipkin.io/

.. code:: python

    from opencensus.ext.zipkin.trace_exporter import ZipkinExporter
    from opencensus.trace import tracer as tracer_module

    tracer = tracer_module.Tracer(exporter=ZipkinExporter(
        service_name='my service',
        host_name='localhost',
        port=9411,
    ))

    with tracer.span(name='hello'):
        print('Hello, World!')

References
----------

* `OpenCensus Project <https://opencensus.io/>`_
* `Zipkin <https://zipkin.io/>`_
