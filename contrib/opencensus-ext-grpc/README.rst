OpenCensus gRPC Integration
============================================================================

OpenCensus provides the implementation of interceptors for both the client side
and server side to instrument the gRPC requests and responses. The client
interceptors are used to create a decorated channel that intercepts client
gRPC calls and server interceptors act as decorators over handlers.

gRPC interceptor is a new feature in the grpcio1.8.0 release, please upgrade
your grpcio to the latest version to use this feature.

For sample usage, please refer to the hello world example in the examples
directory.

More information about the gRPC interceptors please see the `proposal`_.

.. _proposal: https://github.com/mehrdada/proposal/blob/python-interceptors/L13-Python-Interceptors.md

Installation
------------

::

    pip install opencensus-ext-grpc

Usage
-----

.. code:: python

    # TBD
