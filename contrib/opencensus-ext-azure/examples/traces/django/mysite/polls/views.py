from django.http import HttpResponse
import logging

from opencensus.ext.azure.trace_exporter import AzureExporter

# Logging configured through settings.LOGGING in settings.py
logger = logging.getLogger('custom')

# Distributed tracing configured through settings.OPENCENSUS in settings.py
def index(request):
    logger.debug('This is a DEBUG level log entry.')
    logger.info('This is an INFO level log entry.')
    logger.warning('This is a WARNING level log entry.')
    logger.error('This is an ERROR level log entry.')
    logger.critical('This is a CRITICAL level log entry.')
    return HttpResponse("Hello, world. You're at the polls index.")
