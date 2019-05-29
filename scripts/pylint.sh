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

set -ev

# Run pylint on directories
function pylint_dir {
  python -m pip install --upgrade pylint
  find context/ -type f -name "*.py" > output
  find contrib/ -type f -name "*.py" >> output
  find opencensus/ -type f -name "*.py" >> output
  find tests/ -type f -name "*.py" >> output
  find examples/ -type f -name "*.py" >> output

  # TODO fix lint errors
  cat output | xargs pylint || true # ignores errors
  rm -rf output

  return $?
}

pylint_dir
