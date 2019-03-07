OpenCensus SQLAlchemy Integration
============================================================================

You can trace usage of the `sqlalchemy package`_, regardless of the underlying
database, by specifying ``'sqlalchemy'`` to ``trace_integrations``.

.. _SQLAlchemy package: https://pypi.org/project/SQLAlchemy

.. note:: If you enable tracing of SQLAlchemy as well as the underlying database
    driver, you will get duplicate spans. Instead, just trace SQLAlchemy.

Installation
------------

::

    pip install opencensus-ext-sqlalchemy

Usage
-----

.. code:: python

    # TBD
