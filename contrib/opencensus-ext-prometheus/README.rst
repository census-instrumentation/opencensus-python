OpenCensus Prometheus Exporter
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-prometheus.svg
   :target: https://pypi.org/project/opencensus-ext-prometheus/

Installation
------------

::

    pip install opencensus-ext-prometheus

Usage
-----

The OpenCensus `Prometheus`_ Stats Exporter allows users
to export metrics to Prometheus monitoring solution.
The API of this project is still evolving.
The use of vendoring or a dependency management tool is recommended.

.. _Prometheus: https://prometheus.io/

Prometheus Exporter Usage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Prometheus Import
********************

    .. code:: python

        from opencensus.ext.prometheus import stats_exporter as prometheus
        from opencensus.stats import stats as stats_module

Prometheus Prerequisites
***************************

- OpenCensus Python libraries require Python 2.7 or later.
- Prometheus up and running.

Register the Prometheus exporter
***********************************

    .. code:: python

        stats = stats_module.stats
        view_manager = stats.view_manager

        exporter = prometheus.new_stats_exporter(prometheus.Options(namespace="<namespace>"))
        view_manager.register_exporter(exporter)
        ...


Prometheus Code Reference
***************************

In the *examples* folder, you can find all the necessary steps to get the exporter, register a view, put tags on the measure, and see the values against the Prometheus monitoring tool.

For further details for the Prometheus implementation, see the folder *prometheus/stats_exporter*.


+-------------------------------------------------------------------------------+-------------------------------------+
| Path & File                                                                   | Short Description                   |
+===============================================================================+=====================================+
| contrib/opencensus-ext-prometheus/examples/                                   | End to end example                  |
+-------------------------------------------------------------------------------+-------------------------------------+
| contrib/opencensus-ext-prometheus/opencensus/ext/prometheus/stats_exporter/   | Stats implementation for Prometheus |
+-------------------------------------------------------------------------------+-------------------------------------+

