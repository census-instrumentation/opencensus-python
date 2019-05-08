OpenCensus Pyramid Integration
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-pyramid.svg
   :target: https://pypi.org/project/opencensus-ext-pyramid/

Installation
------------

::

    pip install opencensus-ext-pyramid

Usage
-----

In your application, add the pyramid tween and your requests will be
traced.

.. code:: python

    def main(global_config, **settings):
        config = Configurator(settings=settings)

        config.add_tween('opencensus.ext.pyramid'
                         '.pyramid_middleware.OpenCensusTweenFactory')

Additional configuration can be provided, please read
`Customization <https://github.com/census-instrumentation/opencensus-python#customization>`_
for a complete reference.

.. code:: python

    from opencensus.trace import print_exporter
    from opencensus.trace import samplers

    settings = {
        'OPENCENSUS': {
            'TRACE': {
                'EXPORTER': print_exporter.PrintExporter(),
                'SAMPLER': samplers.ProbabilitySampler(rate=0.5),
            }
        }
    }

    config = Configurator(settings=settings)

References
----------

* `OpenCensus Project <https://opencensus.io/>`_
