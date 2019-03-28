OpenCensus Stackdriver Trace Exporter
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-stackdriver.svg
   :target: https://pypi.org/project/opencensus-ext-stackdriver/

Installation
------------

::

    pip install opencensus-ext-stackdriver

Usage
-----

Trace
~~~~~

This example shows how to report the traces to Stackdriver Trace:

.. code:: python

    from opencensus.ext.stackdriver import trace_exporter as stackdriver_exporter
    from opencensus.trace import tracer as tracer_module

    exporter = stackdriver_exporter.StackdriverExporter(
        project_id='your_cloud_project')
    tracer = tracer_module.Tracer(exporter=exporter)

StackdriverExporter requires the google-cloud-trace package. Install
google-cloud-trace using `pip`_ or `pipenv`_:

::

    pip install google-cloud-trace
    pipenv install google-cloud-trace

By default, traces are exported synchronously, which introduces latency during
your code's execution. To avoid blocking code execution, you can initialize
your exporter to use a background thread.

This example shows how to configure OpenCensus to use a background thread:

.. code:: python

    from opencensus.common.transports.async_ import AsyncTransport
    from opencensus.ext.stackdriver import trace_exporter as stackdriver_exporter
    from opencensus.trace import tracer as tracer_module

    exporter = stackdriver_exporter.StackdriverExporter(
        project_id='your_cloud_project', transport=AsyncTransport)
    tracer = tracer_module.Tracer(exporter=exporter)

Stats
~~~~~

The OpenCensus Stackdriver Stats Exporter allows users
to export metrics to Stackdriver Monitoring.
The API of this project is still evolving.
The use of vendoring or a dependency management tool is recommended.

.. _Stackdriver: https://app.google.stackdriver.com/metrics-explorer

Stackdriver Exporter Usage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Stackdriver Import
************************

    .. code:: python

        from opencensus.ext.stackdriver import stats_exporter as stackdriver
        from opencensus.stats import stats as stats_module

Stackdriver Prerequisites
**************************

- OpenCensus Python libraries require Python 2.7 or later.
- Google Cloud Platform account and project.
- Google Stackdriver Monitoring enabled on your project (Need help? `Click here`_).

.. _Click here: https://opencensus.io/codelabs/stackdriver

Register the Stackdriver exporter
**********************************

    .. code:: python

        stats = stats_module.stats
        view_manager = stats.view_manager

        exporter = stackdriver.new_stats_exporter(stackdriver.Options(project_id="<id_value>"))
        view_manager.register_exporter(exporter)
        ...


Stackdriver Code Reference
******************************

In the *examples* folder, you can find all the necessary steps to get the exporter, register a view, put tags on the measure, and see the values against the Stackdriver monitoring tool once you have defined the *project_id*.

For further details for the Stackdriver implementation, see the folder *stackdriver/stats_exporter/*.

+---------------------------------------------------------------------------------+-------------------------------------+
| Path & File                                                                     | Short Description                   |
+=================================================================================+=====================================+
| contrib/opencensus-ext-stackdriver/examples/                                    | End to end example                  |
+---------------------------------------------------------------------------------+-------------------------------------+
| contrib/opencensus-ext-stackdriver/opencensus/ext/stackdriver/stats_exporter/   | Stats implementation for Stackdriver|
+---------------------------------------------------------------------------------+-------------------------------------+

