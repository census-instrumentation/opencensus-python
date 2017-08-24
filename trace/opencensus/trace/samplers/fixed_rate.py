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

import random

from opencensus.trace.samplers.base import Sampler

DEFAULT_SAMPLING_RATE = 0.5


class FixedRateSampler(Sampler):
    """Sample a request at a fixed rate.

    :type rate: float
    :param rate: The rate of sampling.
    """
    def __init__(self, rate=DEFAULT_SAMPLING_RATE):
        if rate > 1 or rate < 0:
            raise ValueError('Rate must between 0 and 1.')

        self.rate = rate

    @property
    def should_sample(self):
        random_number = random.uniform(0, 1)

        if random_number <= self.rate:
            return True
        else:
            return False
