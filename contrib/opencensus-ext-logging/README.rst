OpenCensus logging Integration
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-logging.svg
   :target: https://pypi.org/project/opencensus-ext-logging/

The logging integration enriches the log records with trace ID, span ID and sampling flag.
The following attributes will be added to ``LogRecord``:

    * traceId
    * spanId
    * traceSampled

Note that this only takes effect for loggers created after the integration.

Installation
------------

::

    pip install opencensus-ext-logging

Usage
-----

.. code:: python

    import logging

    from opencensus.trace import config_integration
    from opencensus.trace.samplers import AlwaysOnSampler
    from opencensus.trace.tracer import Tracer

    config_integration.trace_integrations(['logging'])
    logging.basicConfig(format='%(asctime)s traceId=%(traceId)s spanId=%(spanId)s %(message)s')
    tracer = Tracer(sampler=AlwaysOnSampler())

    logger = logging.getLogger(__name__)
    logger.warning('Before the span')
    with tracer.span(name='hello'):
        logger.warning('In the span')
    logger.warning('After the span')


References
----------

* `OpenCensus Project <https://opencensus.io/>`_
