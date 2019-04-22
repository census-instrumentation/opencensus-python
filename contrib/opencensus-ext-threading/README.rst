OpenCensus threading Integration
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-threading.svg
   :target: https://pypi.org/project/opencensus-ext-threading/

OpenCensus can propagate trace across threads when using the threading package.

You can enable Threading integration by specifying ``'threading'`` to ``trace_integrations``.

Installation
------------

::

    pip install opencensus-ext-threading

Usage
-----

.. code:: python

    from opencensus.trace import config_integration

    config_integration.trace_integrations(['threading'])

References
----------

* `OpenCensus Project <https://opencensus.io/>`_
