OpenCensus Azure Monitor Exporters
==================================

OpenCensus Azure Monitor exporters are on the path to deprecation. They will be officially unsupported by September 2024. Please migrate to the `Azure Monitor OpenTelemetry Distro <https://learn.microsoft.com/azure/azure-monitor/app/opentelemetry-enable?tabs=python>`_ for the recommended "one-stop-shop" solution or the `Azure Monitor OpenTelemetry exporters <https://learn.microsoft.com/python/api/overview/azure/monitor-opentelemetry-exporter-readme?view=azure-python-preview>`_ for the more hand-on, configurable solution based on `OpenTelemetry <https://opentelemetry.io/>`_.
Check out the `migration guide <https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-python-opencensus-migrate?tabs=aspnetcore>`_ on how to easily migrate Python code.

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-azure.svg
   :target: https://pypi.org/project/opencensus-ext-azure/

Installation
------------

::

    pip install opencensus-ext-azure

Prerequisites
-------------

* Create an Azure Monitor resource and get the instrumentation key, more information can be found in the official `docs <https://docs.microsoft.com/azure/azure-monitor/app/create-new-resource>`_.
* Place your instrumentation key in a `connection string` and directly into your code.
* Alternatively, you can specify your `connection string` in an environment variable ``APPLICATIONINSIGHTS_CONNECTION_STRING``.
  
Usage
-----

Log
~~~

The **Azure Monitor Log Handler** allows you to export Python logs to `Azure Monitor`_.

This example shows how to send a warning level log to Azure Monitor.

.. code:: python

    import logging

    from opencensus.ext.azure.log_exporter import AzureLogHandler

    logger = logging.getLogger(__name__)
    logger.addHandler(AzureLogHandler(connection_string='InstrumentationKey=<your-instrumentation_key-here>'))
    logger.warning('Hello, World!')

Correlation
###########

You can enrich the logs with trace IDs and span IDs by using the `logging integration <../opencensus-ext-logging>`_.

* Install the `logging integration package <../opencensus-ext-logging>`_ using ``pip install opencensus-ext-logging``.

.. code:: python

    import logging

    from opencensus.ext.azure.log_exporter import AzureLogHandler
    from opencensus.ext.azure.trace_exporter import AzureExporter
    from opencensus.trace import config_integration
    from opencensus.trace.samplers import ProbabilitySampler
    from opencensus.trace.tracer import Tracer

    config_integration.trace_integrations(['logging'])

    logger = logging.getLogger(__name__)

    handler = AzureLogHandler(connection_string='InstrumentationKey=<your-instrumentation_key-here>')
    handler.setFormatter(logging.Formatter('%(traceId)s %(spanId)s %(message)s'))
    logger.addHandler(handler)

    tracer = Tracer(
        exporter=AzureExporter(connection_string='InstrumentationKey=<your-instrumentation_key-here>'),
        sampler=ProbabilitySampler(1.0)
    )

    logger.warning('Before the span')
    with tracer.span(name='test'):
        logger.warning('In the span')
    logger.warning('After the span')

Custom Properties
#################

You can also add custom properties to your log messages in the *extra* keyword argument using the custom_dimensions field.

WARNING: For this feature to work, you need to pass a dictionary to the custom_dimensions field. If you pass arguments of any other type, the logger will ignore them.

.. code:: python

    import logging

    from opencensus.ext.azure.log_exporter import AzureLogHandler

    logger = logging.getLogger(__name__)
    logger.addHandler(AzureLogHandler(connection_string='InstrumentationKey=<your-instrumentation_key-here>'))

    properties = {'custom_dimensions': {'key_1': 'value_1', 'key_2': 'value_2'}}
    logger.warning('action', extra=properties)

Modifying Logs
##############

* You can pass a callback function to the exporter to process telemetry before it is exported.
* Your callback function can return `False` if you do not want this envelope exported.
* Your callback function must accept an `envelope <https://github.com/census-instrumentation/opencensus-python/blob/master/contrib/opencensus-ext-azure/opencensus/ext/azure/common/protocol.py#L86>`_ data type as its parameter.
* You can see the schema for Azure Monitor data types in the envelopes `here <https://github.com/census-instrumentation/opencensus-python/blob/master/contrib/opencensus-ext-azure/opencensus/ext/azure/common/protocol.py>`_.
* The `AzureLogHandler` handles `ExceptionData` and `MessageData` data types.

.. code:: python

    import logging

    from opencensus.ext.azure.log_exporter import AzureLogHandler

    logger = logging.getLogger(__name__)

    # Callback function to append '_hello' to each log message telemetry
    def callback_function(envelope):
        envelope.data.baseData.message += '_hello'
        return True

    handler = AzureLogHandler(connection_string='InstrumentationKey=<your-instrumentation_key-here>')
    handler.add_telemetry_processor(callback_function)
    logger.addHandler(handler)
    logger.warning('Hello, World!')

Events
######

You can send `customEvent` telemetry in exactly the same way you would send `trace` telemetry except using the `AzureEventHandler` instead.

.. code:: python

    import logging

    from opencensus.ext.azure.log_exporter import AzureEventHandler

    logger = logging.getLogger(__name__)
    logger.addHandler(AzureEventHandler(connection_string='InstrumentationKey=<your-instrumentation_key-here>'))
    logger.setLevel(logging.INFO)
    logger.info('Hello, World!')

Metrics
~~~~~~~

The **Azure Monitor Metrics Exporter** allows you to export metrics to `Azure Monitor`_.

.. code:: python

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
        # Set the interval in seconds to 60s, which is the time interval application insights
        # aggregates your metrics
        exporter = metrics_exporter.new_metrics_exporter(
            connection_string='InstrumentationKey=<your-instrumentation-key-here>'
        )
        view_manager.register_exporter(exporter)

        view_manager.register_view(CARROTS_VIEW)
        mmap = stats_recorder.new_measurement_map()
        tmap = tag_map_module.TagMap()

        mmap.measure_int_put(CARROTS_MEASURE, 1000)
        mmap.record(tmap)

        print("Done recording metrics")

    if __name__ == "__main__":
        main()

Performance counters
####################

The exporter also includes a set of performance counters that are exported to Azure Monitor by default.

.. code:: python

    import psutil
    import time

    from opencensus.ext.azure import metrics_exporter

    def main():
        # Performance counters are sent by default. You can disable performance counters by
        # passing in enable_standard_metrics=False into the constructor of
        # new_metrics_exporter() 
        _exporter = metrics_exporter.new_metrics_exporter(
            connection_string='InstrumentationKey=<your-instrumentation-key-here>',
            export_interval=60,
        )
        
        for i in range(100):
            print(psutil.virtual_memory())
            time.sleep(5)

        print("Done recording metrics")

    if __name__ == "__main__":
        main()

Below is a list of performance counters that are currently available:

- Available Memory (bytes)
- CPU Processor Time (percentage)
- Incoming Request Rate (per second)
- Incoming Request Average Execution Time (milliseconds)
- Process CPU Usage (percentage)
- Process Private Bytes (bytes)

Modifying Metrics
#################

* You can pass a callback function to the exporter to process telemetry before it is exported.
* Your callback function can return `False` if you do not want this envelope exported.
* Your callback function must accept an `envelope <https://github.com/census-instrumentation/opencensus-python/blob/master/contrib/opencensus-ext-azure/opencensus/ext/azure/common/protocol.py#L86>`_ data type as its parameter.
* You can see the schema for Azure Monitor data types in the envelopes `here <https://github.com/census-instrumentation/opencensus-python/blob/master/contrib/opencensus-ext-azure/opencensus/ext/azure/common/protocol.py>`_.
* The `MetricsExporter` handles `MetricData` data types.

.. code:: python

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

    # Callback function to only export the metric if value is greater than 0
    def callback_function(envelope):
        return envelope.data.baseData.metrics[0].value > 0

    def main():
        # Enable metrics
        # Set the interval in seconds to 60s, which is the time interval application insights
        # aggregates your metrics
        exporter = metrics_exporter.new_metrics_exporter(
            connection_string='InstrumentationKey=<your-instrumentation-key-here>',
            export_interval=60,
        )
        exporter.add_telemetry_processor(callback_function)
        view_manager.register_exporter(exporter)

        view_manager.register_view(CARROTS_VIEW)
        mmap = stats_recorder.new_measurement_map()
        tmap = tag_map_module.TagMap()

        mmap.measure_int_put(CARROTS_MEASURE, 1000)
        mmap.record(tmap)

        print("Done recording metrics")

    if __name__ == "__main__":
        main()

Trace
~~~~~

The **Azure Monitor Trace Exporter** allows you to export `OpenCensus`_ traces to `Azure Monitor`_.

This example shows how to send a span "hello" to Azure Monitor.

 .. code:: python

    from opencensus.ext.azure.trace_exporter import AzureExporter
    from opencensus.trace.samplers import ProbabilitySampler
    from opencensus.trace.tracer import Tracer

    tracer = Tracer(
        exporter=AzureExporter(
            connection_string='InstrumentationKey=<your-instrumentation-key-here>'
        ),
        sampler=ProbabilitySampler(1.0)
    )

    with tracer.span(name='hello'):
        print('Hello, World!')

Integrations
############

OpenCensus also supports several `integrations <https://github.com/census-instrumentation/opencensus-python#integration>`_ which allows OpenCensus to integrate with third party libraries.

This example shows how to integrate with the `requests <https://2.python-requests.org/en/master/>`_ library.

* Install the `requests integration package <../opencensus-ext-requests>`_ using ``pip install opencensus-ext-requests``.

.. code:: python

    import requests

    from opencensus.ext.azure.trace_exporter import AzureExporter
    from opencensus.trace import config_integration
    from opencensus.trace.samplers import ProbabilitySampler
    from opencensus.trace.tracer import Tracer

    config_integration.trace_integrations(['requests'])
    tracer = Tracer(
        exporter=AzureExporter(
            connection_string='InstrumentationKey=<your-instrumentation-key-here>',
        ),
        sampler=ProbabilitySampler(1.0),
    )
    with tracer.span(name='parent'):
        response = requests.get(url='https://www.wikipedia.org/wiki/Rabbit')

Modifying Traces
################

* You can pass a callback function to the exporter to process telemetry before it is exported.
* Your callback function can return `False` if you do not want this envelope exported.
* Your callback function must accept an `envelope <https://github.com/census-instrumentation/opencensus-python/blob/master/contrib/opencensus-ext-azure/opencensus/ext/azure/common/protocol.py#L86>`_ data type as its parameter.
* You can see the schema for Azure Monitor data types in the envelopes `here <https://github.com/census-instrumentation/opencensus-python/blob/master/contrib/opencensus-ext-azure/opencensus/ext/azure/common/protocol.py>`_.
* The `AzureExporter` handles `Data` data types.

.. code:: python

    import requests

    from opencensus.ext.azure.trace_exporter import AzureExporter
    from opencensus.trace import config_integration
    from opencensus.trace.samplers import ProbabilitySampler
    from opencensus.trace.tracer import Tracer

    config_integration.trace_integrations(['requests'])

    # Callback function to add os_type: linux to span properties
    def callback_function(envelope):
        envelope.data.baseData.properties['os_type'] = 'linux'
        return True

    exporter = AzureExporter(
        connection_string='InstrumentationKey=<your-instrumentation-key-here>'
    )
    exporter.add_telemetry_processor(callback_function)
    tracer = Tracer(exporter=exporter, sampler=ProbabilitySampler(1.0))
    with tracer.span(name='parent'):
        response = requests.get(url='https://www.wikipedia.org/wiki/Rabbit')
        
Integrate with Azure Functions
##############################

Users who want to capture custom telemetry in Azure Functions environments are encouraged to used the OpenCensus Python Azure Functions `extension <https://github.com/census-ecosystem/opencensus-python-extensions-azure/tree/main/extensions/functions#opencensus-python-azure-functions-extension>`_. More details can be found in this `document <https://docs.microsoft.com/azure/azure-functions/functions-reference-python?tabs=application-level#log-custom-telemetry>`_.

References
----------

* `Azure Monitor <https://docs.microsoft.com/azure/azure-monitor/>`_
* `Official Microsoft Docs <https://learn.microsoft.com/previous-versions/azure/azure-monitor/app/opencensus-python>`_
* `Examples <https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-azure/examples>`_
* `OpenCensus Project <https://opencensus.io/>`_

.. _Azure Monitor: https://docs.microsoft.com/azure/azure-monitor/
.. _OpenCensus: https://github.com/census-instrumentation/opencensus-python/
