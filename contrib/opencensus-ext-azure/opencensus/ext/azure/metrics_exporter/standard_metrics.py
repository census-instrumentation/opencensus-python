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
import psutil

from opencensus.metrics.export.gauge import DerivedDoubleGauge
from opencensus.metrics.export.gauge import DerivedLongGauge
from opencensus.metrics.export.gauge import Registry
from opencensus.metrics.export.metric_producer import MetricProducer

logger = logging.getLogger(__name__)
PROCESS = psutil.Process()

# Namespaces used in Azure Monitor
AVAILABLE_MEMORY = "\\Memory\\Available Bytes"
PRIVATE_BYTES = "\\Process(??APP_WIN32_PROC??)\\Private Bytes"
PROCESSOR_TIME = "\\Processor(_Total)\\% Processor Time"
PROCESS_TIME = "\\Process(??APP_WIN32_PROC??)\\% Processor Time"


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
        process = psutil.Process()
        return process.memory_info().rss
    except Exception:
        logger.exception('Error handling get process private bytes.')


def get_process_private_bytes_metric():
    """ Returns a derived gauge for private bytes for the current process

    Private bytes for the current process is measured by the Resident Set
    Size, which is the non-swapped physical memory a process has used.

    :rtype: :class:`opencensus.metrics.export.gauge.DerivedLongGauge`
    :return: The gauge representing the private bytes metric
    """
    gauge = DerivedLongGauge(
        PRIVATE_BYTES,
        'Amount of memory process has used in bytes',
        'byte',
        [])
    gauge.create_default_time_series(get_process_private_bytes)
    return gauge


def get_processor_time():
    cpu_times_percent = psutil.cpu_times_percent()
    return 100 - cpu_times_percent.idle


def get_processor_time_metric():
    """ Returns a derived gauge for the processor time.

    Processor time is defined as a float representing the current system
    wide CPU utilization minus idle CPU time as a percentage. Idle CPU
    time is defined as the time spent doing nothing.

    :rtype: :class:`opencensus.metrics.export.gauge.DerivedDoubleGauge`
    :return: The gauge representing the processor time metric
    """
    gauge = DerivedDoubleGauge(
        PROCESSOR_TIME,
        'Processor time as a percentage',
        'percentage',
        [])
    gauge.create_default_time_series(get_processor_time)
    return gauge


def get_process_cpu_usage():
    try:
        # In the case of a process running on multiple threads on different CPU
        # cores, the returned value of cpu_percent() can be > 100.0. The actual
        # value that is return from this function should be capped at 100.
        return min(PROCESS.cpu_percent(), 100.0)
    except Exception:
        logger.exception('Error handling get process cpu usage.')


def get_process_cpu_usage_metric():
    """ Returns a derived gauge for the CPU usage for the current process as a percentage.

    :rtype: :class:`opencensus.metrics.export.gauge.DerivedDoubleGauge`
    :return: The gauge representing the process cpu usage metric
    """
    gauge = DerivedDoubleGauge(
        PROCESS_TIME,
        'Processor time as a percentage',
        'percentage',
        [])
    gauge.create_default_time_series(get_process_cpu_usage)
    # From the psutil docs: the first time this method is called with interval
    # = None it will return a meaningless 0.0 value which you are supposed to
    # ignore. Call cpu_percent() once so that the subsequent calls from the
    # gauge will be meaningful.
    PROCESS.cpu_percent()
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
        self.registry.add_gauge(get_processor_time_metric())
        self.registry.add_gauge(get_process_cpu_usage_metric())

    def get_metrics(self):
        return self.registry.get_metrics()


producer = AzureStandardMetricsProducer()
