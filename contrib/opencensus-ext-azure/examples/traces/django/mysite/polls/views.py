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

from django.http import HttpResponse

# Logging configured through settings.LOGGING in settings.py
logger = logging.getLogger('custom')


# Distributed tracing configured through settings.OPENCENSUS in settings.py
def index(request):
    logger.debug('This is a DEBUG level log entry.')
    logger.info('This is an INFO level log entry.')
    logger.warning('This is a WARNING level log entry.')
    logger.error('This is an ERROR level log entry.')
    logger.critical('This is a CRITICAL level log entry.')
    return HttpResponse("Hello, world. You're at the polls index.")
