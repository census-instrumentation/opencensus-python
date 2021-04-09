OpenCensus OC-Agent Exporter
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-ocagent.svg
   :target: https://pypi.org/project/opencensus-ext-ocagent/

Installation
------------

::

    pip install opencensus-ext-ocagent

Usage
-----

Stats
~~~~~

.. code:: python

    from opencensus.ext.ocagent import stats_exporter as ocagent_stats_exporter

    ocagent_stats_exporter.new_stats_exporter(
        service_name='service_name',
        endpoint='localhost:55678')

References
----------

* `OpenCensus Project <https://opencensus.io/>`_
* `OpenCensus Services <https://github.com/census-instrumentation/opencensus-service>`_
