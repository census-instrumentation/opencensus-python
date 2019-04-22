OpenCensus requests Integration
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-requests.svg
   :target: https://pypi.org/project/opencensus-ext-requests/

OpenCensus can trace HTTP requests made with the `requests package`_. The request URL,
method, and status will be collected.

You can enable requests integration by specifying ``'requests'`` to ``trace_integrations``.

It's possible to configure a list of URL you don't want traced. By default the request to exporter
won't be traced. It's configurable by giving an array of hostname/port to the attribute
``blacklist_hostnames`` in OpenCensus context's attributes:

Only the hostname must be specified if only the hostname is specified in the URL request.

.. _Requests package: https://pypi.python.org/pypi/requests

Installation
------------

::

    pip install opencensus-ext-requests

Usage
-----

.. code:: python

    import requests
    from opencensus.trace import config_integration
    from opencensus.trace.tracer import Tracer

    if __name__ == '__main__':
        config_integration.trace_integrations(['requests'])
        tracer = Tracer()
        with tracer.span(name='parent'):
            response = requests.get(url='https://www.wikipedia.org/wiki/Rabbit')

References
----------

* `OpenCensus Project <https://opencensus.io/>`_
