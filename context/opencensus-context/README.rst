OpenCensus Runtime Context
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-context.svg
   :target: https://pypi.org/project/opencensus-context/

The **OpenCensus Runtime Context** provides in-process context propagation.
By default, ``thread local storage`` is used for Python 2.7, 3.4 and 3.5;
``contextvars`` is used for Python >= 3.6, which provides ``asyncio`` support.

Installation
------------

This library is installed by default with ``opencensus``, there is no need
to install it explicitly.

Usage
-----

In most cases context propagation happens automatically within a process,
following the control flow of threads and asynchronous coroutines. The runtime
context is a dictionary stored in a `context variable <https://docs.python.org/3/library/contextvars.html>`_
when available, and in `thread local storage <https://docs.python.org/2/library/threading.html#threading.local>`_
otherwise.

There are cases where you may want to propagate the context explicitly:

Explicit Thread Creation
~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    from threading import Thread
    from opencensus.common.runtime_context import RuntimeContext

    def work(name):
        # here you will get the context from the parent thread
        print(RuntimeContext)

    thread = Thread(
        # propagate context explicitly
        target=RuntimeContext.with_current_context(work),
        args=('foobar',),
    )
    thread.start()
    thread.join()

Thread Pool
~~~~~~~~~~~

.. code:: python

    from multiprocessing.dummy import Pool as ThreadPool
    from opencensus.common.runtime_context import RuntimeContext

    def work(name):
        # here you will get the context from the parent thread
        print(RuntimeContext)

    pool = ThreadPool(2)
    # propagate context explicitly
    pool.map(RuntimeContext.with_current_context(work), [
        'bear',
        'cat',
        'dog',
        'horse',
        'rabbit',
    ])
    pool.close()
    pool.join()

References
----------

* `Examples <https://github.com/census-instrumentation/opencensus-python/tree/master/context/opencensus-context/examples>`_
* `OpenCensus Project <https://opencensus.io/>`_
