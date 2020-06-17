# Copyright 2017, OpenCensus Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os

from django.conf import settings

from celery import Celery
from celery.signals import setup_logging
from opencensus.ext.azure.log_exporter import AzureLogHandler

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

app = Celery('app')
app.config_from_object('django.conf:settings', namespace='CELERY')
# app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.autodiscover_tasks()

# def add_azure_log_handler_to_logger(logger, propagate=True):
#     """
#     Given a logger, add a AzureLogHandler to it
#     :param logger:
#     :param propagate:
#     :return:
#     """
#     formatter = logging.Formatter("[Celery/%(processName)s] %(message)s")
#     # Azure Handler:
#     azure_log_handler = AzureLogHandler()
#     azure_log_handler.setFormatter(formatter)
#     azure_log_handler.setLevel(logging.INFO)
#     logger.addHandler(azure_log_handler)
#     logger.setLevel(logging.INFO)
#     logger.propagate = propagate

# @setup_logging.connect
# def setup_loggers(*args, **kwargs):
#     """
#     Using the celery "setup_logging" signal to override and fully define the logging configuration for Celery
#     :param args:
#     :param kwargs:
#     :return:
#     """
#     # Configure Celery logging from the Django settings' logging configuration
#     from logging.config import dictConfig
#     from django.conf import settings
#     dictConfig(settings.LOGGING)

#     # Test the root logger (configured in django settings to log to Azure as well
#     logger = logging.getLogger('root')
#     logger.warning('TRYING LOGGING FROM [%s]' % logger.name)

#     # Configure the Celery top level logger
#     logger = logging.getLogger('celery')
#     # Add a local file log handler to make sure we capture every message locally
#     logger.addHandler(logging.FileHandler("/data/log/worker/importer.log"))
#     # In addition, also manually add a AzureLogHandler to it (duplicate with the root's handler)
#     logger = add_azure_log_handler_to_logger(logger, propagate=False)
#     # Log a test warning message
#     logger.warning('TRYING LOGGING FROM [%s]' % logger.name)

#     # Log a test warning message from a lower-level celery logger
#     logger = logging.getLogger('celery.task')
#     logger.warning('TRYING LOGGING FROM [%s]' % logger.name)

#     # Log a test warning message from a specific django app task logger
#     logger = logging.getLogger('etl.tasks')
#     logger.warning('TRYING LOGGING FROM [%s]' % logger.name)
