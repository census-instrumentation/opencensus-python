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

"""Module containing base class for samplers."""


class Sampler(object):
    """Base class for opencensus trace request samplers.

    Subclasses of :class:`Sampler` must override :meth:`should_sample`.
    """

    @property
    def should_sample(self):
        """Determine whether to sample this request or not."""
        raise NotImplementedError
