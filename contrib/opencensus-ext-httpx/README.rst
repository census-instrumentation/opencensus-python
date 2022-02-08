OpenCensus httpx Integration
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-httpx.svg
   :target: https://pypi.org/project/opencensus-ext-httpx/

OpenCensus can trace HTTP requests made with the `httpx package <https://www.python-httpx.org>`_. The request URL,
method, and status will be collected.

You can enable httpx integration by specifying ``'httpx'`` to ``trace_integrations``.

Only the hostname must be specified if only the hostname is specified in the URL request.


Installation
------------

::

    pip install opencensus-ext-httpx

Usage
-----

.. code:: python

    import httpx
    from opencensus.trace import config_integration
    from opencensus.trace.tracer import Tracer

    if __name__ == '__main__':
        config_integration.trace_integrations(['httpx'])
        tracer = Tracer()
        with tracer.span(name='parent'):
            response = httpx.get(url='https://www.example.org')

References
----------

* `OpenCensus Project <https://opencensus.io/>`_
