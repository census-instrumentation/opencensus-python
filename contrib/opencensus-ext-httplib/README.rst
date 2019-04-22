OpenCensus httplib Integration
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-httplib.svg
   :target: https://pypi.org/project/opencensus-ext-httplib/

OpenCensus can trace HTTP requests made with the httplib library.

You can enable requests integration by specifying ``'httplib'`` to ``trace_integrations``.

It's possible to configure a list of URL you don't want traced. See requests integration
for more information. The only difference is that you need to specify hostname and port
every time.

Installation
------------

::

    pip install opencensus-ext-httplib

Usage
-----

.. code:: python

    import requests
    from opencensus.trace import config_integration
    from opencensus.trace.tracer import Tracer

    config_integration.trace_integrations(['httplib'])
    tracer = Tracer()

    with tracer.span(name='parent'):
        response = requests.get('https://www.wikipedia.org/wiki/Rabbit')

References
----------

* `OpenCensus Project <https://opencensus.io/>`_
