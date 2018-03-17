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

from google.cloud import monitoring
from opencensus.stats.exporters import stackdriver_exporter

HOST_PORT = 'localhost:50051'


def main():

    client = monitoring.Client()
    exporter = stackdriver_exporter.StackdriverExporter(client, "opencensus-python")

    metric = client.metric(
        type_= 'serviceruntime.googleapis.com/api/request_latencies',
        labels={}
    )
    resource = client.resource(
        type_='gce_instance',
        labels={
            'instance_id': '1234567890123456789',
            'zone': 'us-central1-f',
        }
    )

    '''metric_descriptor = exporter.translate_to_stackdriver(metric)'''
    '''metric_descriptor.create()'''
    client.write_point(metric, resource, 3.14)


if __name__ == '__main__':
    main()
