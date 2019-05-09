OpenCensus gevent helper
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-ext-gevent.svg
   :target: https://pypi.org/project/opencensus-ext-gevent/

Installation
------------

::

    pip install opencensus-ext-gevent

Usage
-----

As gevent is to date `incompatible <https://github.com/gevent/gevent/issues/1407>`_ with
the new context variables the **OpenCensus gevent helper** configures OpenCensus to use
a compatible thread based runtime context implementation.

No action apart from installing the package is needed as it listens to events
`emitted by gevent  <http://www.gevent.org/api/gevent.monkey.html#plugins>`_ once
patching via ``patch_all`` is complete.


Warning
-------

OpenCensus itself is completely compatible with gevent. Be aware though that not all
available OpenCensus integrations are compatible.

You should  check this on a case by case basis.


References
----------

* `OpenCensus Project <https://opencensus.io/>`_
* `gevent <https://www.gevent.org/>`_
