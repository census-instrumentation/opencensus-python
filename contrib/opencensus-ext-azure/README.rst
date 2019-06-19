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
        from opencensus.metrics.export import meter
        from opencensus.metrics.export import measure
        from opencensus.metrics.export import metrics_producer

        mp = metrics_producer.metrics_producer
        meter = mp.meter
        _measure = meter.create_measure("test_count",
                                        measure.MeasureType.LONG,
                                        "test_desc",
                                        "test_unit",
                                        measure.AggregationType.COUNT)

        def main():
            metrics_exporter.new_metrics_exporter(export_interval=2)

            measurements = []
            for i in range(10):
                measurements.append(_measure.create_long_measurement(i))
            
            meter.record(_measure, measurements)
            time.sleep(5)
            print("Done recording metrics")

        if __name__ == "__main__":
            main()

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
