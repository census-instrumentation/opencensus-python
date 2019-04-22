OpenCensus PyMySQL Integration
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-pymysql.svg
   :target: https://pypi.org/project/opencensus-ext-pymysql/

Installation
------------

::

    pip install opencensus-ext-pymysql

Usage
-----

.. code:: python

    from opencensus.trace import config_integration

    config_integration.trace_integrations(['pymysql'])

References
----------

* `OpenCensus Project <https://opencensus.io/>`_

