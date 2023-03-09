OpenCensus FastAPI Integration
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-fastapi.svg
   :target: https://pypi.org/project/opencensus-ext-fastapi/

Installation
------------

::

    pip install opencensus-ext-fastapi

Usage
-----

.. code:: python

    from fastapi import FastAPI
    from opencensus.ext.fastapi.fastapi_middleware import FastAPIMiddleware

    app = FastAPI(__name__)
    app.add_middleware(FastAPIMiddleware)

    @app.get('/')
    def hello():
        return 'Hello World!'

Additional configuration can be provided, please read
`Customization <https://github.com/census-instrumentation/opencensus-python#customization>`_
for a complete reference.

.. code:: python

    app.add_middleware(
        FastAPIMiddleware,
        excludelist_paths=["paths"],
        excludelist_hostnames=["hostnames"],
        sampler=sampler,
        exporter=exporter,
        propagator=propagator,
    )


References
----------

* `OpenCensus Project <https://opencensus.io/>`_
