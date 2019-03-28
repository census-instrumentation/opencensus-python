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

To configure the sampler, exporter, and propagator, pass the instances
into the pyramid settings

.. code:: python

    from opencensus.trace import print_exporter
    from opencensus.trace.propagation import google_cloud_format
    from opencensus.trace.samplers import probability

    settings = {}
    settings['OPENCENSUS_TRACE'] = {
        'EXPORTER': print_exporter.PrintExporter(),
        'SAMPLER': probability.ProbabilitySampler(rate=0.5),
        'PROPAGATOR': google_cloud_format.GoogleCloudFormatPropagator(),
    }

    config = Configurator(settings=settings)
