NOT TO USE YET:: OpenCensus FastAPI Integration || this is still in development, can't be used yet
==================================================================================================

|pypi|

.. |pypi| image:: https://pypi.org/project/pipprojectpkg/
   :target: https://pypi.org/project/pipprojectpkg/

Installation
------------

::

    pip install pipprojectpkg

Usage
-----

.. code:: python

   from opencensus.ext.azure.trace_exporter import AzureExporter
   from opencensus.trace.samplers import ProbabilitySampler
   from fastAPIMiddleware import FastAPIMiddleware
   import uvicorn
   from fastapi import FastAPI, Request

   app = FastAPI()

   middleware = FastAPIMiddleware(
       app,
       exporter=AzureExporter(connection_string="InstrumentationKey=<InstrumentationKey>"),
       sampler=ProbabilitySampler(rate=1.0),
   )

   @app.get("/")
   async def root(request:Request):
       return {"message": request.client.host}


   if __name__=="__main__":
       uvicorn.run("fastAPISample:app", port=8888, reload=True, debug=True, workers=3)


Additional configuration can be provided, please read
`Customization <https://github.com/census-instrumentation/opencensus-python#customization>`_
for a complete reference.

.. code:: python

    app.config['OPENCENSUS'] = {
        'TRACE': {
            'SAMPLER': 'opencensus.trace.samplers.ProbabilitySampler(rate=1)',
            'EXPORTER': '''opencensus.ext.ocagent.trace_exporter.TraceExporter(
                service_name='foobar',
            )''',
        }
    }

References
----------

* `OpenCensus Project <https://opencensus.io/>`_
