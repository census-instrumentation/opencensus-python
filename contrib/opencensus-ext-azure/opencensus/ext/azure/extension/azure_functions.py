# Copyright 2021, OpenCensus Authors
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

from logging import Logger
from typing import Dict, List, Optional

from azure.functions import (
    AppExtensionBase,
    Context,
)
from opencensus.trace import config_integration
from opencensus.trace.propagation.trace_context_http_header_format import (
    TraceContextPropagator,
)
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer

from ..trace_exporter import AzureExporter

class OpenCensusExtension(AppExtensionBase):
    """Extension for Azure Functions integration to export traces into Azure
    Monitor. Ensure the following requirements are met:
    1. Azure Functions version is greater or equal to v3.0.15584
    2. App setting PYTHON_ENABLE_WORKER_EXTENSIONS is set to 1
    """

    @classmethod
    def init(cls):
        cls._exporter: Optional[AzureExporter] = None
        cls._trace_integrations: List[str] = []

    @classmethod
    def configure(cls,
                  libraries: List[str],
                  connection_string: Optional[str] = None,
                  *args,
                  **kwargs):
        """Configure libraries for integrating into OpenCensus extension.
        Initialize an Azure Exporter that will write traces to AppInsights.
        :type libraries: List[str]
        :param libraries: the libraries opencensus-ext-* that need to be
            integrated into OpenCensus tracer. (e.g. ['requests'])
        :type connection_string: Optional[str]
        :param connection_string: the connection string of azure exporter
            to write into. If this is set to None, the extension will use
            an instrumentation connection string from your app settings.
        """
        cls._trace_integrations = config_integration.trace_integrations(
            libraries
        )

        cls._exporter = AzureExporter(connection_string=connection_string)

    @classmethod
    def pre_invocation_app_level(cls,
                                 logger: Logger,
                                 context: Context,
                                 func_args: Dict[str, object] = {},
                                 *args,
                                 **kwargs) -> None:
        """An implementation of pre invocation hooks on Function App's level.
        The Python Worker Extension Interface is defined in
        https://github.com/Azure/azure-functions-python-library/
        blob/dev/azure/functions/extension/app_extension_base.py
        """
        if not cls._exporter:
            logger.warning(
                'Please call OpenCensusExtension.configure() after the import '
                'statement to ensure AzureExporter is setup correctly.'
            )
            return

        span_context = TraceContextPropagator().from_headers({
            "traceparent": context.trace_context.Traceparent,
            "tracestate": context.trace_context.Tracestate
        })

        tracer = Tracer(
            span_context=span_context,
            exporter=cls._exporter,
            sampler=ProbabilitySampler(1.0)
        )

        setattr(context, 'tracer', tracer)

    @classmethod
    def post_invocation_app_level(cls,
                                  logger: Logger,
                                  context: Context,
                                  func_args: Dict[str, object],
                                  func_ret: Optional[object],
                                  *args,
                                  **kwargs) -> None:
        """An implementation of post invocation hooks on Function App's level.
        The Python Worker Extension Interface is defined in
        https://github.com/Azure/azure-functions-python-library/
        blob/dev/azure/functions/extension/app_extension_base.py
        """
        if getattr(context, 'tracer', None):
            del context.tracer
