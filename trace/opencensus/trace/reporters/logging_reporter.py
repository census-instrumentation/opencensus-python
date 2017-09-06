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

"""Export the spans data to python logging."""

import logging

from opencensus.trace.reporters import base


class LoggingReporter(base.Reporter):
    """A reporter to export the spans data to python logging. Also can use
    handlers like CloudLoggingHandler to log to Stackdriver Logging API.

    :type handler: :class:`logging.handler`
    :param handler: the handler to attach to the global handler

    Example:

    .. code-block:: python

        import google.cloud.logging
        from google.cloud.logging.handlers import CloudLoggingHandler
        from opencensus.trace.reporters import logging_reporter

        client = google.cloud.logging.Client()
        cloud_handler = CloudLoggingHandler(client)
        reporter = logging_reporter.LoggingReporter(handler=cloud_handler)

        reporter.report(your_spans_list)

    Or initialize a context tracer with the logging reporter, then the traces
    will be reported to logging when finished.
    """

    def __init__(self, handler=None):
        self.logger = logging.getLogger()

        if handler is None:
            handler = logging.StreamHandler()

        self.handler = handler
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def report(self, trace):
        """
        :type traces: dict
        :param traces: Trace collected.
        """
        self.logger.info(trace)
