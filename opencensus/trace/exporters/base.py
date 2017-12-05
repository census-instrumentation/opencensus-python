# Copyright 2016-17, OpenCensus Authors
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

"""Module containing base class for exporters."""


class Exporter(object):
    """Base class for opencensus trace request exporters.

    Subclasses of :class:`Exporter` must override :meth:`export`.
    """
    def emit(self, trace):
        """Emit the trace."""
        raise NotImplementedError

    def export(self, trace):
        """Export the trace. Send trace to transport, and transport will call
        exporter.emit() to actually send the trace to the specified tracing
        backend.
        """
        raise NotImplementedError
