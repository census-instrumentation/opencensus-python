OpenCensus Azure Monitor Exporters
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

Log
~~~

The **Azure Monitor Log Handler** allows you to export Python logs to `Azure Monitor`_.

This example shows how to send a warning level log to Azure Monitor.

* Create an Azure Monitor resource and get the instrumentation key, more information can be found `here <https://docs.microsoft.com/azure/azure-monitor/app/create-new-resource>`_.
* Put the instrumentation key in ``APPINSIGHTS_INSTRUMENTATIONKEY`` environment variable.
* You can also specify the instrumentation key explicitly in the code, which will take priority over a set environment variable.

.. code:: python

    import logging

    from opencensus.ext.azure.log_exporter import AzureLogHandler

    logger = logging.getLogger(__name__)
    logger.addHandler(AzureLogHandler())
    logger.warning('Hello, World!')

You can enrich the logs with trace IDs and span IDs by using the `logging integration <../opencensus-ext-logging>`_.

* Create an Azure Monitor resource and get the instrumentation key, more information can be found `here <https://docs.microsoft.com/azure/azure-monitor/app/create-new-resource>`_.
* Install the `logging integration package <../opencensus-ext-logging>`_ using ``pip install opencensus-ext-logging``.
* Put the instrumentation key in ``APPINSIGHTS_INSTRUMENTATIONKEY`` environment variable.
* You can also specify the instrumentation key explicitly in the code, which will take priority over a set environment variable.

.. code:: python

    import logging

    from opencensus.ext.azure.log_exporter import AzureLogHandler
    from opencensus.ext.azure.trace_exporter import AzureExporter
    from opencensus.trace import config_integration
    from opencensus.trace.samplers import ProbabilitySampler
    from opencensus.trace.tracer import Tracer

    config_integration.trace_integrations(['logging'])

    logger = logging.getLogger(__name__)

    handler = AzureLogHandler()
    handler.setFormatter(logging.Formatter('%(traceId)s %(spanId)s %(message)s'))
    logger.addHandler(handler)

    tracer = Tracer(exporter=AzureExporter(), sampler=ProbabilitySampler(1.0))

    logger.warning('Before the span')
    with tracer.span(name='test'):
        logger.warning('In the span')
    logger.warning('After the span')

Metrics
~~~~~~~

The **Azure Monitor Metrics Exporter** allows you to export metrics to `Azure Monitor`_.

* Create an Azure Monitor resource and get the instrumentation key, more information can be found `here <https://docs.microsoft.com/azure/azure-monitor/app/create-new-resource>`_.
* Put the instrumentation key in ``APPINSIGHTS_INSTRUMENTATIONKEY`` environment variable.
* You can also specify the instrumentation key explicitly in the code, which will take priority over a set environment variable.

.. code:: python

    import time

    from opencensus.ext.azure import metrics_exporter
    from opencensus.stats import aggregation as aggregation_module
    from opencensus.stats import measure as measure_module
    from opencensus.stats import stats as stats_module
    from opencensus.stats import view as view_module
    from opencensus.tags import tag_map as tag_map_module

    stats = stats_module.stats
    view_manager = stats.view_manager
    stats_recorder = stats.stats_recorder

    CARROTS_MEASURE = measure_module.MeasureInt("carrots",
                                                "number of carrots",
                                                "carrots")
    CARROTS_VIEW = view_module.View("carrots_view",
                                    "number of carrots",
                                    [],
                                    CARROTS_MEASURE,
                                    aggregation_module.CountAggregation())

    def main():
        # Enable metrics
        # Set the interval in seconds in which you want to send metrics
        exporter = metrics_exporter.new_metrics_exporter()
        view_manager.register_exporter(exporter)

        view_manager.register_view(CARROTS_VIEW)
        mmap = stats_recorder.new_measurement_map()
        tmap = tag_map_module.TagMap()

        mmap.measure_int_put(CARROTS_MEASURE, 1000)
        mmap.record(tmap)
        # Default export interval is every 15.0s
        # Your application should run for at least this amount
        # of time so the exporter will meet this interval
        # Sleep can fulfill this
        time.sleep(60)

        print("Done recording metrics")

    if __name__ == "__main__":
        main()

The exporter also includes a set of standard metrics that are exported to Azure Monitor by default.

.. code:: python

    import psutil
    import time

    from opencensus.ext.azure import metrics_exporter

    def main():
        # All you need is the next line. You can disable standard metrics by
        # passing in enable_standard_metrics=False into the constructor of
        # new_metrics_exporter() 
        _exporter = metrics_exporter.new_metrics_exporter()
        
        for i in range(100):
            print(psutil.virtual_memory())
            time.sleep(5)

        print("Done recording metrics")

    if __name__ == "__main__":
        main()

Below is a list of standard metrics that are currently available:

- Available Memory (bytes)
- CPU Processor Time (percentage)
- Outgoing Request Rate (per second)
- Process CPU Usage (percentage)
- Process Private Bytes (bytes)

Trace
~~~~~

The **Azure Monitor Trace Exporter** allows you to export `OpenCensus`_ traces to `Azure Monitor`_.

This example shows how to send a span "hello" to Azure Monitor.

* Create an Azure Monitor resource and get the instrumentation key, more information can be found `here <https://docs.microsoft.com/azure/azure-monitor/app/create-new-resource>`_.
* Put the instrumentation key in ``APPINSIGHTS_INSTRUMENTATIONKEY`` environment variable.
* You can also specify the instrumentation key explicitly in the code, which will take priority over a set environment variable.

.. code:: python

    from opencensus.ext.azure.trace_exporter import AzureExporter
    from opencensus.trace.samplers import ProbabilitySampler
    from opencensus.trace.tracer import Tracer

    tracer = Tracer(exporter=AzureExporter(), sampler=ProbabilitySampler(1.0))

    with tracer.span(name='hello'):
        print('Hello, World!')

You can also specify the instrumentation key explicitly in the code.

* Create an Azure Monitor resource and get the instrumentation key, more information can be found `here <https://docs.microsoft.com/azure/azure-monitor/app/create-new-resource>`_.
* Install the `requests integration package <../opencensus-ext-requests>`_ using ``pip install opencensus-ext-requests``.
* Put the instrumentation key in ``APPINSIGHTS_INSTRUMENTATIONKEY`` environment variable.
* You can also specify the instrumentation key explicitly in the code, which will take priority over a set environment variable.

.. code:: python

    import requests

    from opencensus.ext.azure.trace_exporter import AzureExporter
    from opencensus.trace import config_integration
    from opencensus.trace.samplers import ProbabilitySampler
    from opencensus.trace.tracer import Tracer

    config_integration.trace_integrations(['requests'])
    tracer = Tracer(
        exporter=AzureExporter(
            # TODO: replace this with your own instrumentation key.
            instrumentation_key='00000000-0000-0000-0000-000000000000',
        ),
        sampler=ProbabilitySampler(1.0),
    )
    with tracer.span(name='parent'):
        response = requests.get(url='https://www.wikipedia.org/wiki/Rabbit')


References
----------

* `Azure Monitor <https://docs.microsoft.com/azure/azure-monitor/>`_
* `Examples <https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-azure/examples>`_
* `OpenCensus Project <https://opencensus.io/>`_

.. _Azure Monitor: https://docs.microsoft.com/azure/azure-monitor/
.. _OpenCensus: https://github.com/census-instrumentation/opencensus-python/
