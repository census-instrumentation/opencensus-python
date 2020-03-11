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

from __future__ import absolute_import

import os

import nox


def _install_dev_packages(session):
    session.install('-e', 'context/opencensus-context')
    session.install('-e', 'contrib/opencensus-correlation')
    session.install('-e', '.')

    session.install('-e', 'contrib/opencensus-ext-azure')
    session.install('-e', 'contrib/opencensus-ext-datadog')
    session.install('-e', 'contrib/opencensus-ext-dbapi')
    session.install('-e', 'contrib/opencensus-ext-django')
    session.install('-e', 'contrib/opencensus-ext-flask')
    session.install('-e', 'contrib/opencensus-ext-gevent')
    session.install('-e', 'contrib/opencensus-ext-grpc')
    session.install('-e', 'contrib/opencensus-ext-httplib')
    session.install('-e', 'contrib/opencensus-ext-jaeger')
    session.install('-e', 'contrib/opencensus-ext-logging')
    session.install('-e', 'contrib/opencensus-ext-mysql')
    session.install('-e', 'contrib/opencensus-ext-ocagent')
    session.install('-e', 'contrib/opencensus-ext-postgresql')
    session.install('-e', 'contrib/opencensus-ext-prometheus')
    session.install('-e', 'contrib/opencensus-ext-pymongo')
    session.install('-e', 'contrib/opencensus-ext-pymysql')
    session.install('-e', 'contrib/opencensus-ext-pyramid')
    session.install('-e', 'contrib/opencensus-ext-requests')
    session.install('-e', 'contrib/opencensus-ext-sqlalchemy')
    session.install('-e', 'contrib/opencensus-ext-stackdriver')
    session.install('-e', 'contrib/opencensus-ext-threading')
    session.install('-e', 'contrib/opencensus-ext-zipkin')
    session.install('-e', 'contrib/opencensus-ext-google-cloud-clientlibs')


def _install_test_dependencies(session):
    session.install('mock==3.0.5')
    session.install('pytest==4.6.4')

    session.install('retrying')
    session.install('unittest2')


@nox.session(python=['3.6'])
def system(session):
    """Run the system test suite."""

    # Sanity check: Only run system tests if the environment variable is set.
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', ''):
        session.skip('Credentials must be set via environment variable.')

    # Install test dependencies.
    _install_test_dependencies(session)

    # Install dev packages into the virtualenv's dist-packages.
    _install_dev_packages(session)

    # Run py.test against the system tests.
    session.run(
        'py.test',
        '-s',
        'tests/system/',
        *session.posargs
    )
