import logging

from opencensus.ext.azure.log_exporter import AzureLogHandler

logger = logging.getLogger(__name__)
# TODO: you need to specify the instrumentation key in a connection string
# and place it in the APPLICATIONINSIGHTS_CONNECTION_STRING
# environment variable.
logger.addHandler(AzureLogHandler())
logger.warning('action', {'key-1': 'value-1', 'key-2': 'value2'})