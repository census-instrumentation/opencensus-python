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


This example will send the span "hello" to the Azure Monitoring resource specified
in the ``APPINSIGHTS_INSTRUMENTATIONKEY`` environment variable.

You need to provision an Azure Monitor resource and get the instrumentation key,
more information can be founded `here <https://docs.microsoft.com/azure/azure-monitor/app/create-new-resource>`_.

.. code:: python
    from opencensus.ext.azure.trace_exporter import AzureExporter
    from opencensus.trace import tracer as tracer_module

    tracer = tracer_module.Tracer(exporter=AzureExporter())

    if __name__ == '__main__':
        with tracer.span(name='hello'):
            print('Hello, World!')

