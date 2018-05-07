# Copyright 2018, OpenCensus Authors
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

from google.cloud import monitoring
from google.cloud.monitoring import MetricDescriptor
from opencensus.stats.exporters import stackdriver_exporter
from opencensus.stats import measure
from opencensus.stats import view
from opencensus.stats import aggregation
from opencensus.stats import stats_recorder
from opencensus.stats import view_manager
from opencensus.stats import stats


def main():
    views = []

    client = monitoring.Client()
    exporter = stackdriver_exporter.StackDriverExporter(client, "opencensus-python-202919", resource="global")

    boundaries = [0, 1/16, 1/32]

    video_size = measure.BaseMeasure("my.org/measure/video_size", "size of processed videos", "MBy")
    my_view = view.View("my.org/views/video_size_cum", "processed video size over time", [], video_size, aggregation.DistributionAggregation(boundaries))
    views = views.append(my_view)

    my_stats_recorder = stats.Stats().stats_recorder
    my_stats_recorder.new_measurement_map().measure_int_put(video_size, 25648)

    exporter.emit(views, datapoint=25648)
    exporter.export(views)




if __name__ == '__main__':
    main()
