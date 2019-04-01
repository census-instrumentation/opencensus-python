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

import requests

from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.tweens import MAIN
from pyramid.view import view_config


@view_config(route_name='hello')
def hello(request):
    return Response('Hello world!')


@view_config(route_name='trace_requests')
def trace_requests(request):
    response = requests.get('http://www.google.com')
    return Response(str(response.status_code))


def main(global_config, **settings):
    config = Configurator(settings=settings)

    config.add_route('hello', '/')
    config.add_route('trace_requests', '/requests')

    config.add_tween('opencensus.trace.ext.pyramid'
                     '.pyramid_middleware.OpenCensusTweenFactory',
                     over=MAIN)

    config.scan()

    return config.make_wsgi_app()
