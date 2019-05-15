OpenCensus logging Integration
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-logging.svg
   :target: https://pypi.org/project/opencensus-ext-logging/

Installation
------------

::

    pip install opencensus-ext-logging

Usage
-----

.. code:: python

    import logging

    from opencensus.trace import config_integration
    from opencensus.trace.samplers import AlwaysOffSampler
    from opencensus.trace.tracer import Tracer

    config_integration.trace_integrations(['logging'])
    logging.basicConfig(format='%(asctime)-15s traceId=%(traceId)s spanId=%(spanId)s %(message)s')
    tracer = Tracer(sampler=AlwaysOffSampler())

    logger = logging.getLogger(__name__)
    logger.warning('Before the span')
    with tracer.span(name='hello'):
        logger.warning('In the span')
    logger.warning('After the span')


References
----------

* `OpenCensus Project <https://opencensus.io/>`_
