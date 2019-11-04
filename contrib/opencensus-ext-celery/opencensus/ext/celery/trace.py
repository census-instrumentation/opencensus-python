import logging

from celery.signals import (
    after_task_publish,
    before_task_publish,
    task_failure,
    task_prerun,
    task_success,
)

from opencensus.trace import attributes_helper, execution_context
from opencensus.trace import span as span_module
from opencensus.trace import tracer as tracer_module

log = logging.getLogger(__name__)

MODULE_NAME = 'celery'

CELERY_METADATA_THREAD_LOCAL_KEY = 'celery_trace_metadata'
SPAN_THREAD_LOCAL_KEY = 'celery_span'
TRACING_HEADER_NAME = '__tracing_metadata__'

tracing_settings = {}


def trace_integration(tracer=None):
    if tracer is not None:
        # The execution_context tracer should never be None - if it has not
        # been set it returns a no-op tracer. Most code in this library does
        # not handle None being used in the execution context.
        execution_context.set_opencensus_tracer(tracer)
        exporter = tracer.exporter
        propagator = tracer.propagator
        sampler = tracer.sampler

        tracing_settings.update({'sampler': sampler,
                                 'exporter': exporter,
                                 'propagator': propagator})

    """Wrap the celery library to trace it."""
    log.info('Integrated module: {}'.format(MODULE_NAME))


class CeleryMetaWrapper(object):
    def __init__(self, meta=None):
        self.meta = meta or get_celery_meta()

    def get(self, key):
        return self.meta.get(key)


def get_celery_meta():
    """Get Celery metadata from thread local."""
    return execution_context.get_opencensus_attr(
        CELERY_METADATA_THREAD_LOCAL_KEY
    )


def get_celery_span():
    """Get Celery span from thread local."""
    return execution_context.get_opencensus_attr(SPAN_THREAD_LOCAL_KEY)


@before_task_publish.connect
def before_task_publish_handler(headers=None, **kwargs):
    try:
        tracer = execution_context.get_opencensus_tracer()
        span = tracer.start_span()
        span.name = 'celery.publish.{}'.format(kwargs.get('sender'))
        span.span_kind = span_module.SpanKind.CLIENT

        tracing_metadata = \
            tracing_settings.get('propagator').to_headers(tracer.span_context)
        headers[TRACING_HEADER_NAME] = tracing_metadata
    except Exception:  # noqa
        log.error('Failed to trace task', exc_info=True)


@after_task_publish.connect
def after_task_publish_handler(**kwargs):  # noqa kwargs
    try:
        tracer = execution_context.get_opencensus_tracer()
        tracer.end_span()
    except Exception:  # noqa
        log.error('Failed to trace task', exc_info=True)


@task_prerun.connect
def task_prerun_handler(task, **kwargs):
    trace_metadata = getattr(task.request, TRACING_HEADER_NAME, {})
    if trace_metadata:
        execution_context.set_opencensus_attr(
            CELERY_METADATA_THREAD_LOCAL_KEY,
            trace_metadata)

        try:
            propagator = tracing_settings.get('propagator')
            # Start tracing this request
            span_context = propagator.from_headers(
                CeleryMetaWrapper(trace_metadata))

            # Reload the tracer with the new span context
            tracer = tracer_module.Tracer(
                span_context=span_context,
                sampler=tracing_settings.get('sampler'),
                exporter=tracing_settings.get('exporter'),
                propagator=propagator)

            # Span name is being set at process_view
            span = tracer.start_span()
            span.span_kind = span_module.SpanKind.SERVER
            span.name = 'celery.consume.{}'.format(kwargs.get('sender').name)

            execution_context.set_opencensus_attr(
                SPAN_THREAD_LOCAL_KEY, span)

        except Exception:  # noqa
            log.error('Failed to trace request', exc_info=True)


@task_success.connect
def task_success_handler(**kwargs):  # noqa kwargs
    try:
        span = get_celery_span()
        span.add_attribute(
            attribute_key='result',
            attribute_value='success')

        tracer = execution_context.get_opencensus_tracer()
        tracer.end_span()
        tracer.finish()
    except Exception:  # noqa
        log.error('Failed to trace request', exc_info=True)


@task_failure.connect
def task_failure_handler(traceback=None, **kwargs):  # noqa kwargs
    try:
        span = get_celery_span()
        span.add_attribute(
            attribute_key='result',
            attribute_value='failure')
        span.add_attribute(attributes_helper.COMMON_ATTRIBUTES['STACKTRACE'],
                           str(traceback))

        tracer = execution_context.get_opencensus_tracer()
        tracer.end_span()
        tracer.finish()
    except Exception:  # noqa
        log.error('Failed to trace request', exc_info=True)
    pass
