OpenCensus Stackdriver Trace Exporter
============================================================================

Installation
------------

::

    pip install opencensus-ext-stackdriver

Usage
-----

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

        stats = stats_module.Stats()
        view_manager = stats.view_manager

        exporter = stackdriver.new_stats_exporter(stackdriver.Options(project_id="<id_value>"))
        view_manager.register_exporter(exporter)
        ...


Stackdriver Code Reference
******************************

In the *examples* folder, you can find all the necessary steps to get the exporter, register a view, put tags on the measure, and see the values against the Stackdriver monitoring tool once you have defined the *project_id*.

For further details for the Stackdriver implementation, see the folder *stackdriver_exporter.py*.

+----------------------------------------------------+-------------------------------------+
| Path & File                                        | Short Description                   |
+====================================================+=====================================+
| examples/stats/exporter/stackdriver.py             | End to end example                  |
+----------------------------------------------------+-------------------------------------+
| opencensus/ext/stackdriver/stats_exporters/        | Stats implementation for Stackdriver|
+----------------------------------------------------+-------------------------------------+

