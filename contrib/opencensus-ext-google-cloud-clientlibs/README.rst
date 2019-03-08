OpenCensus Google Cloud Client Libraries Integration
============================================================================

OpenCensus can trace HTTP and gRPC requests made with the `Cloud client libraries`_.
The request URL, method, and status will be collected.

You can enable Google Cloud client libraries integration by specifying ``'google_cloud_clientlibs'`` to ``trace_integrations``.

.. _Cloud client libraries: https://github.com/GoogleCloudPlatform/google-cloud-python#google-cloud-python-client

Installation
------------

::

    pip install opencensus-ext-google-cloud-clientlibs

Usage
-----

.. code:: python

    # TBD
