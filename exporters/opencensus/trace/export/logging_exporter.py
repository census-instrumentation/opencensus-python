# Copyright 2017 Google Inc.
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


class LoggingExporter(object):
    """An exporter to export the spans data to python logging. Also can use
    handlers like CloudLoggingHandler to log to Stackdriver Logging API.

    :type handler: :class:`logging.handler`
    :param handler: the handler to attach to the global handler
    
    Example:
    
    .. code-block:: python

        import google.cloud.logging
        from google.cloud.logging.handlers import CloudLoggingHandler
        from opencensus.trace.export import logging_exporter
        
        client = google.cloud.logging.Client()
        cloud_handler = CloudLoggingHandler(client)
        exporter = logging_exporter.LoggingExporter(handler=cloud_handler)
        
        exporter.export(your_spans_list)
    """

    def __init__(self, handler=None):
        self.logger = logging.getLogger()

        if handler is None:
            handler = logging.StreamHandler()

        self.handler = handler
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def export(self, spans_list):
        for span in spans_list:
            self.logger.info(str(span))
