from threading import Thread
from opencensus.common.runtime_context import RuntimeContext

RuntimeContext.register_slot('correlation_context', lambda: dict())


def withcc(fn):
    fork = RuntimeContext.correlation_context.copy()
    def callcc(*args, **kwargs):
        try:
            snapshot = RuntimeContext.correlation_context
            RuntimeContext.correlation_context = fork
            return fn(*args, **kwargs)
        finally:
            RuntimeContext.correlation_context = snapshot
    return callcc


def work(name):
    print(RuntimeContext)
    RuntimeContext.correlation_context['name'] = name
    print(RuntimeContext)


if __name__ == '__main__':
    print(RuntimeContext)
    RuntimeContext.correlation_context['test'] = True
    print(RuntimeContext)

    # by default context is not propagated to worker thread
    thread = Thread(target=work, args=('foo',))
    thread.start()
    thread.join()

    # user can propagate context explicitly (withcc = with current context)
    thread = Thread(target=withcc(work), args=('foo',))
    thread.start()
    thread.join()
