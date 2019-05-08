# Copyright 2018, OpenCensus Authors
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

# If this is not a CircleCI tag, no-op.
if [[ -z "$CIRCLE_TAG" ]]; then
  echo "This is not a release tag. Doing nothing."
  exit 0
fi

BASEDIR=$PWD

echo -e "[pypi]" >> ~/.pypirc
echo -e "username = $PYPI_USERNAME" >> ~/.pypirc
echo -e "password = $PYPI_PASSWORD" >> ~/.pypirc

# Ensure that we have the latest versions of Twine, Wheel, and Setuptools.
python3 -m pip install --upgrade twine wheel setuptools

# Build the distributions.
python3 setup.py bdist_wheel

for d in context/*/ contrib/*/ ; do
  pushd .
  cd "$d"
  python3 setup.py bdist_wheel --dist-dir "$BASEDIR/dist/"
  popd
done

# Upload the distributions.
for p in dist/* ; do
  twine upload $p
done
