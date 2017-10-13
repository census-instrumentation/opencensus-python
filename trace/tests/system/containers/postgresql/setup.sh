#!/usr/bin/env bash
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

# Pull the postgres docker image
echo "Pulling postgres container..."
docker pull postgres

# Start running the postgres server
echo "Start running postgres container..."
docker run --name=systest_postgresql \
    -d -e POSTGRES_PASSWORD=$SYSTEST_POSTGRES_PASSWORD postgres

# Wait for the postgres container running
until nc -z -v -w30 192.168.9.2 5432
do
  echo "Waiting for postgres database connection..."
  # Wait for 5 seconds before check again
  sleep 5
done
