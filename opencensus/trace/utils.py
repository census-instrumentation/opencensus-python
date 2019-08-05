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

import re

from google.rpc import code_pb2
from opencensus.trace import execution_context
from opencensus.trace.status import Status

# By default the blacklist urls are not tracing, currently just include the
# health check url. The paths are literal string matched instead of regular
# expressions. Do not include the '/' at the beginning of the path.
DEFAULT_BLACKLIST_PATHS = [
    '_ah/health',
]

# Pattern for matching the 'https://', 'http://', 'ftp://' part.
URL_PATTERN = '^(https?|ftp):\\/\\/'


def get_func_name(func):
    """Return a name which includes the module name and function name."""
    func_name = getattr(func, '__name__', func.__class__.__name__)
    module_name = func.__module__

    if module_name is not None:
        module_name = func.__module__
        return '{}.{}'.format(module_name, func_name)

    return func_name


def disable_tracing_url(url, blacklist_paths=None):
    """Disable tracing on the provided blacklist paths, by default not tracing
    the health check request.

    If the url path starts with the blacklisted path, return True.

    :type blacklist_paths: list
    :param blacklist_paths: Paths that not tracing.

    :rtype: bool
    :returns: True if not tracing, False if tracing.
    """
    if blacklist_paths is None:
        blacklist_paths = DEFAULT_BLACKLIST_PATHS

    # Remove the 'https?|ftp://' if exists
    url = re.sub(URL_PATTERN, '', url)

    # Split the url by the first '/' and get the path part
    url_path = url.split('/', 1)[1]

    for path in blacklist_paths:
        if url_path.startswith(path):
            return True

    return False


def disable_tracing_hostname(url, blacklist_hostnames=None):
    """Disable tracing for the provided blacklist URLs, by default not tracing
    the exporter url.

    If the url path starts with the blacklisted path, return True.

    :type blacklist_hostnames: list
    :param blacklist_hostnames: URL that not tracing.

    :rtype: bool
    :returns: True if not tracing, False if tracing.
    """
    if blacklist_hostnames is None:
        # Exporter host_name are not traced by default
        _tracer = execution_context.get_opencensus_tracer()
        try:
            blacklist_hostnames = [
                '{}:{}'.format(
                    _tracer.exporter.host_name,
                    _tracer.exporter.port
                )
            ]
        except(AttributeError):
            blacklist_hostnames = []

    return url in blacklist_hostnames


def status_from_http_code(http_code):
    """Returns equivalent status from http status code
    based on OpenCensus specs.

    :type http_code: int
    :param http_code: HTTP request status code.

    :rtype: int
    :returns: A instance of :class: `~opencensus.trace.status.Status`.
    """
    grpc_code = None
    if http_code <= 199:
        grpc_code = code_pb2.UNKNOWN
    elif http_code >= 200 and http_code <= 399:
        grpc_code = code_pb2.OK
    elif http_code == 400:
        grpc_code = code_pb2.INVALID_ARGUMENT
    elif http_code == 504:
        grpc_code = code_pb2.DEADLINE_EXCEEDED
    elif http_code == 404:
        grpc_code = code_pb2.NOT_FOUND
    elif http_code == 403:
        grpc_code = code_pb2.PERMISSION_DENIED
    elif http_code == 401:
        grpc_code = code_pb2.UNAUTHENTICATED
    elif http_code == 429:
        grpc_code = code_pb2.RESOURCE_EXHAUSTED
    elif http_code == 501:
        grpc_code = code_pb2.UNIMPLEMENTED
    elif http_code == 503:
        grpc_code = code_pb2.UNAVAILABLE
    else:
        grpc_code = code_pb2.UNKNOWN

    return Status(grpc_code)
