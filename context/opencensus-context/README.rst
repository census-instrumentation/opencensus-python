OpenCensus Runtime Context
============================================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opencensus-context.svg
   :target: https://pypi.org/project/opencensus-context/

Installation
------------

This library comes by default when you install OpenCensus, there is no need
to install it explicitly.

Usage
-----

The **OpenCensus Runtime Context** provides the in-process context propagation.
By default, thread local storage is used for Python 2.7, 3.4 and 3.5;
contextvars is used for Python >= 3.6, which provides asyncio support.

By default, context would flow in the same thread and async task. There are
cases where you may want to propagate the context explicitly:

* Explicit thread creation:

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

* Thread pool:

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
