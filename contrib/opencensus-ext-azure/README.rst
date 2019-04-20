OpenCensus Azure Monitor Trace Exporter
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-azure.svg
   :target: https://pypi.org/project/opencensus-ext-azure/

Installation
------------

::

    pip install opencensus-ext-azure

Usage
-----

Trace
~~~~~

The **Azure Monitor Trace Exporter** allows you to export traces to `Azure Monitor`_.

.. _Azure Monitor: https://docs.microsoft.com/azure/azure-monitor/


This example shows how to send a span "hello" to Azure Monitor.

* Provision an Azure Monitor resource and get the instrumentation key, more information can be found `here <https://docs.microsoft.com/azure/azure-monitor/app/create-new-resource>`_.
* Put the instrumentation key in ``APPINSIGHTS_INSTRUMENTATIONKEY`` environment variable.


.. code:: python

    from opencensus.ext.azure.trace_exporter import AzureExporter
    from opencensus.trace import tracer as tracer_module

    tracer = tracer_module.Tracer(exporter=AzureExporter())

    if __name__ == '__main__':
        with tracer.span(name='hello'):
            print('Hello, World!')

You can also specify the instrumentation key explicitly in the code.

.. code:: python

    import requests

    from opencensus.ext.azure.common import Options
    from opencensus.ext.azure.trace_exporter import AzureExporter
    from opencensus.trace import config_integration
    from opencensus.trace.tracer import Tracer

    if __name__ == '__main__':
        config_integration.trace_integrations(['requests'])
        tracer = Tracer(exporter=AzureExporter(Options(
            # TODO: replace this with your own instrumentation key
            instrumentation_key='00000000-0000-0000-0000-000000000000',
            timeout=29.9,
        )))
        with tracer.span(name='parent'):
            with tracer.span(name='child'):
                response = requests.get(url='http://localhost:8080/')

Take a look at the `examples <https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-azure/examples>`_ for more information.
