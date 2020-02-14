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

from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_map as tag_map_module

stats = stats_module.stats
view_manager = stats.view_manager
stats_recorder = stats.stats_recorder

request_measure = measure_module.MeasureInt("added tasks",
                                            "number of added tasks",
                                            "tasks")
request_view = view_module.View("added tasks",
                                "number of tasks",
                                ["application_type"],
                                request_measure,
                                aggregation_module.CountAggregation())
view_manager.register_view(request_view)
mmap = stats_recorder.new_measurement_map()
tmap = tag_map_module.TagMap()
tmap.insert("application_type", "flask")
tmap.insert("os_type", "linux")
