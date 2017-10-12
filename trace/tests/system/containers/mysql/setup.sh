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

# Pull the mysql docker image
echo "Pulling mysql container..."
docker pull mysql

# Start running the mysql server
echo "Start running mysql container..."
docker run --name=systest_mysql \
    -d -e MYSQL_ROOT_PASSWORD=$SYSTEST_MYSQL_PASSWORD mysql

# Wait for the mysql container running
until nc -z -v -w30 192.168.9.2 3306
do
  echo "Waiting for mysql database connection..."
  # wait for 5 seconds before check again
  sleep 5
done
