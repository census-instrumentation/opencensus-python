# Copyright 2019, OpenCensus Authors
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
import psutil

from opencensus.metrics.export.gauge import DerivedLongGauge
from opencensus.metrics.export.gauge import Registry
from opencensus.metrics.export.metric_producer import MetricProducer

logger = logging.getLogger(__name__)


# Namespaces used in Azure Monitor
AVAILABLE_MEMORY = "\\Memory\\Available Bytes"
PRIVATE_BYTES = "\\Process(??APP_WIN32_PROC??)\\Private Bytes"


def get_available_memory():
    return psutil.virtual_memory().available


def get_available_memory_metric():
    """ Returns a derived gauge for available memory

    Available memory is defined as memory that can be given instantly to
    processes without the system going into swap.

    :rtype: :class:`opencensus.metrics.export.gauge.DerivedLongGauge`
    :return: The gauge representing the available memory metric
    """
    gauge = DerivedLongGauge(
        AVAILABLE_MEMORY,
        'Amount of available memory in bytes',
        'byte',
        [])
    gauge.create_default_time_series(get_available_memory)
    return gauge

def get_process_private_bytes():
    try:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss
    except psutil.NoSuchProcess as ex:
        logger.error('Error: Process does not exist %s.', ex)
    except psutil.AccessDenied as ex:
        logger.error('Error: Cannot access process information %s.', ex)

def get_process_private_bytes_metric():
    """ Returns a derived gauge for private bytes for the current process

    Private bytes for the current process is measured by the Resident Set
    Size, which is the non-swapped physical memory a process has used.

    :rtype: :class:`opencensus.metrics.export.gauge.DerivedLongGauge`
    :return: The gauge representing the private bytes metric
    """
    gauge = DerivedLongGauge(
        PRIVATE_BYTES,
        'Amount of available memory in bytes',
        'byte',
        [])
    gauge.create_default_time_series(get_process_private_bytes)
    return gauge

class AzureStandardMetricsProducer(MetricProducer):
    """Implementation of the producer of standard metrics.

    Includes Azure specific standard metrics, implemented
    using gauges.
    """
    def __init__(self):
        self.registry = Registry()
        self.registry.add_gauge(get_available_memory_metric())
        self.registry.add_gauge(get_process_private_bytes_metric())

    def get_metrics(self):
        return self.registry.get_metrics()


producer = AzureStandardMetricsProducer()
