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

import psutil

from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module


# Definitions taken from psutil docs
# https://psutil.readthedocs.io/en/latest/
class StandardMetricsType(object):
    # Memory that can be given instantly to
    # processes without the system going into swap
    AVAILABLE_MEMORY = "\\Memory\\Available Bytes"


class StandardMetricsRecorder():

    def __init__(self):
        self.measurement_map = None
        self.measure_map = {}
        self.setup()

    def setup(self):
        """ Populates and returns a MeasurementMap with standard metric
        related measures. Standard metrics are defined in StandardMetricsType
        """

        # Sets up stats related objects to begin
        # recording standard metrics
        stats_ = stats_module.stats
        view_manager = stats_.view_manager
        stats_recorder = stats_.stats_recorder

        # Standard metrics uses a separate instance of MeasurementMap
        # from regular metrics but still shares the same underlying
        # map data in the context. This way, the processing during
        # record is handled through a separate data structure but
        # the storage only uses one single data structure
        # Uniqueness should be based off the name of the view and
        # measure. A warning message in the logs will be shown
        # if there are duplicate names
        self.measurement_map = stats_recorder.new_measurement_map()

        # TODO: Use MeasureInt once [#565] is fixed
        available_memory_measure = measure_module.MeasureFloat("Available memory",
            "Amount of available memory in bytes",
            "bytes")
        self.measure_map[StandardMetricsType.AVAILABLE_MEMORY] = available_memory_measure
        available_memory_view = view_module.View(StandardMetricsType.AVAILABLE_MEMORY,
            "Amount of available memory in bytes",
            [],
            available_memory_measure,
            aggregation_module.LastValueAggregation())
        view_manager.register_view(available_memory_view)

    def record_standard_metrics(self):
        # Function called periodically to record standard metrics
        
        # Available memory
        vmem = psutil.virtual_memory()
        available_memory = vmem.available
        available_memory_measure = self.measure_map[StandardMetricsType.AVAILABLE_MEMORY]
        if available_memory_measure is not None:
            self.measurement_map.measure_int_put(available_memory_measure, available_memory)
            
        self.measurement_map.record()
