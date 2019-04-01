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

import unittest


def func_to_trace():
    print('Test simple tracing...')


class TestBasicTrace(unittest.TestCase):

    def test_tracer(self):
        import json

        from opencensus.trace import tracer as tracer_module
        from opencensus.trace import file_exporter
        from opencensus.trace.samplers import always_on
        from opencensus.trace.propagation import google_cloud_format

        trace_id = 'f8739df974a4481f98748cd92b27177d'
        span_id = '6e0c63257de34c92'
        trace_option = 1

        trace_header = '{}/{};o={}'.format(trace_id, span_id, trace_option)

        sampler = always_on.AlwaysOnSampler()
        exporter = file_exporter.FileExporter()
        propagator = google_cloud_format.GoogleCloudFormatPropagator()
        span_context = propagator.from_header(header=trace_header)

        tracer = tracer_module.Tracer(
            span_context=span_context,
            sampler=sampler,
            exporter=exporter,
            propagator=propagator
        )

        with tracer.span(name='root_span') as root:
            func_to_trace()
            parent_span_id = root.span_id
            with root.span(name='child_span'):
                func_to_trace()

        tracer.finish()

        file = open(file_exporter.DEFAULT_FILENAME, 'r')
        trace_json = json.loads(file.read())

        spans = trace_json.get('spans')

        self.assertEqual(trace_json.get('traceId'), trace_id)
        self.assertEqual(len(spans), 2)

        self.assertSetEqual(
            {ss['displayName']['value'] for ss in spans},
            {'child_span', 'root_span'})

        for span in spans:
            if span['displayName']['value'] == 'root_span':
                self.assertEqual(span['parentSpanId'], span_id)
                self.assertEqual(span['childSpanCount'], 1)
            else:
                self.assertEqual(span['displayName']['value'], 'child_span')
                self.assertEqual(span['parentSpanId'], parent_span_id)
                self.assertEqual(span['childSpanCount'], 0)
