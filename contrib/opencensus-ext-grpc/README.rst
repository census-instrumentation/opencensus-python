OpenCensus gRPC Integration
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-grpc.svg
   :target: https://pypi.org/project/opencensus-ext-grpc/

OpenCensus provides the implementation of interceptors for both the client side
and server side to instrument the gRPC requests and responses. The client
interceptors are used to create a decorated channel that intercepts client gRPC
calls and server interceptors act as decorators over handlers.

gRPC interceptors are a new feature as of the 1.8.0 ``grpcio`` release, please
upgrade ``grpcio`` to the latest version to use this feature.

For sample usage, please refer to the hello world `example`_.

.. _example: ../examples/

More information about the gRPC interceptors please see the `proposal`_.

.. _proposal: https://github.com/grpc/proposal/blob/master/L13-python-interceptors.md

Installation
------------

::

    pip install opencensus-ext-grpc


References
----------

* `gRPC <https://grpc.io/>`_
* `OpenCensus Project <https://opencensus.io/>`_
