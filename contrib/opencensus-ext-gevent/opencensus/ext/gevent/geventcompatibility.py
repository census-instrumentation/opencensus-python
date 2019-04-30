import logging
import gevent.monkey


def patch_opencensus(event):
    # Switch from the default runtime context using ContextVar to one
    # using thread locals. Needed until gevent supports ContextVar.
    # See https://github.com/gevent/gevent/issues/1407
    import opencensus.common.runtime_context as runtime_context

    if not gevent.monkey.is_module_patched("contextvars"):
        runtime_context.RuntimeContext = (
            runtime_context._ThreadLocalRuntimeContext()
        )

        logging.warning("OpenCensus patched for gevent compatibility")
    else:
        logging.warning(
            "OpenCensus is already compatible with your gevent version. "
            "Feel free to uninstall the opencensus-ext-gevent package."
        )
