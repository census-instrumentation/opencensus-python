OpenCensus requests Integration
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-aiohttp.svg
   :target: https://pypi.org/project/opencensus-ext-aiohttp/

OpenCensus can trace asynchronous HTTP requests made with the `aiohttp package`_. The request URL,
method, and status will be collected.

You can enable aiohttp integration by specifying ``'aiohttp'`` to ``trace_integrations``.

It's possible to configure a list of URL you don't want traced, anf it's configurable by giving an array of
hostname/port to the attribute ``excludelist_hostnames`` in OpenCensus context's attributes:


.. _aiohttp package: https://pypi.python.org/pypi/aiohttp

Installation
------------

::

    pip install opencensus-ext-requests

Usage
-----

.. code:: python

    import asyncio
    from aiohttp import ClientSession
    from opencensus.trace import config_integration
    from opencensus.trace.tracer import Tracer


    config_integration.trace_integrations(['aiohttp'])

    async def main():
        tracer = Tracer()
        with tracer.span(name='parent'):
            client_session = ClientSession()
            async with client_session.get(url='https://www.wikipedia.org/wiki/Rabbit') as response:
                await response.read()


    asyncio.run(main())

References
----------

* `OpenCensus Project <https://opencensus.io/>`_
