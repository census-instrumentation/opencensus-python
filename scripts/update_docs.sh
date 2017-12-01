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

set -ev

# Build docs
function build_docs {
    rm -rf docs/build/
    cp README.rst docs/trace/usage.rst
    sed -i '1s/.*/OpenCensus Trace for Python/' docs/trace/usage.rst
    sed -i '2s/.*/===========================/' docs/trace/usage.rst
    make html
    return $?
}

build_docs

cp -R docs/build/html/* docs/
rm -rf docs/build
