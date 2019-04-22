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

The **Azure Monitor Trace Exporter** allows you to export `OpenCensus`_ traces to `Azure Monitor`_.

.. _Azure Monitor: https://docs.microsoft.com/azure/azure-monitor/
.. _OpenCensus: https://github.com/census-instrumentation/opencensus-python/

This example shows how to send a span "hello" to Azure Monitor.

* Create an Azure Monitor resource and get the instrumentation key, more information can be found `here <https://docs.microsoft.com/azure/azure-monitor/app/create-new-resource>`_.
* Put the instrumentation key in ``APPINSIGHTS_INSTRUMENTATIONKEY`` environment variable.


.. code:: python

    from opencensus.ext.azure.trace_exporter import AzureExporter
    from opencensus.trace import tracer as tracer_module

    tracer = tracer_module.Tracer(exporter=AzureExporter())

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
            # TODO: replace this with your own instrumentation key.
            instrumentation_key='00000000-0000-0000-0000-000000000000',
            timeout=29.9,
        )))
        with tracer.span(name='parent'):
            response = requests.get(url='https://www.wikipedia.org/wiki/Rabbit')

References
----------

* `Azure Monitor <https://docs.microsoft.com/azure/azure-monitor/>`_
* `Examples <https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-azure/examples>`_
* `OpenCensus Project <https://opencensus.io/>`_
