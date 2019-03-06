OpenCensus httplib Integration
============================================================================

Census can trace HTTP requests made with the httplib library.

You can enable requests integration by specifying ``'httplib'`` to ``trace_integrations``.

It's possible to configure a list of URL you don't want traced. See requests integration
for more information. The only difference is that you need to specify hostname and port
every time.

Installation
------------

::

    pip install opencensus-ext-httplib

Usage
-----

.. code:: python

    # TBD
