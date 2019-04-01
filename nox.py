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

import nox
import os


def _install_dev_packages(session):
    session.install('-e', 'context/opencensus-context')
    session.install('-e', 'contrib/opencensus-correlation')
    session.install('-e', '.')

    session.install('-e', 'contrib/opencensus-ext-dbapi')
    session.install('-e', 'contrib/opencensus-ext-django')
    session.install('-e', 'contrib/opencensus-ext-flask')
    session.install('-e', 'contrib/opencensus-ext-grpc')
    session.install('-e', 'contrib/opencensus-ext-httplib')
    session.install('-e', 'contrib/opencensus-ext-jaeger')
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


@nox.session
@nox.parametrize('py', ['2.7', '3.4', '3.5', '3.6'])
def unit(session, py):
    """Run the unit test suite."""

    # Run unit tests against all supported versions of Python.
    session.interpreter = 'python{}'.format(py)

    # Install all test dependencies.
    session.install('-r', 'requirements-test.txt')

    # Install dev packages.
    _install_dev_packages(session)

    # Run py.test against the unit tests.
    session.run(
        'py.test',
        '--quiet',
        '--cov=opencensus', '--cov=contrib',
        '--cov-append',
        '--cov-config=.coveragerc',
        '--cov-report=',
        '--cov-fail-under=97',
        'tests/unit/', 'contrib/',
        *session.posargs
    )


@nox.session
@nox.parametrize('py', ['2.7', '3.6'])
def system(session, py):
    """Run the system test suite."""

    # Sanity check: Only run system tests if the environment variable is set.
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', ''):
        session.skip('Credentials must be set via environment variable.')

    # Run the system tests against latest Python 2 and Python 3 only.
    session.interpreter = 'python{}'.format(py)

    # Set the virtualenv dirname.
    session.virtualenv_dirname = 'sys-' + py

    # Install all test dependencies.
    session.install('-r', 'requirements-test.txt')

    # Install dev packages into the virtualenv's dist-packages.
    _install_dev_packages(session)

    # Run py.test against the system tests.
    session.run(
        'py.test',
        '-s',
        'tests/system/',
        *session.posargs
    )


@nox.session
def lint(session):
    """Run flake8.
    Returns a failure if flake8 finds linting errors or sufficiently
    serious code quality issues.
    """
    session.interpreter = 'python3.6'
    session.install('flake8')

    # Install dev packages.
    _install_dev_packages(session)

    session.run(
        'flake8',
        '--exclude=contrib/opencensus-ext-ocagent/opencensus/ext/ocagent/trace_exporter/gen/',
        'context/', 'contrib/', 'opencensus/', 'tests/', 'examples/')


@nox.session
def lint_setup_py(session):
    """Verify that setup.py is valid (including RST check)."""
    session.interpreter = 'python3.6'
    session.install('docutils', 'pygments')
    session.run(
        'python', 'setup.py', 'check', '--restructuredtext', '--strict')


@nox.session
def cover(session):
    """Run the final coverage report.
    This outputs the coverage report aggregating coverage from the unit
    test runs (not system test runs), and then erases coverage data.
    """
    session.interpreter = 'python3.6'
    session.install('coverage', 'pytest-cov')
    session.run('coverage', 'report', '--show-missing', '--fail-under=100')
    session.run('coverage', 'erase')


@nox.session
def docs(session):
    """Build the docs."""

    # Build docs against the latest version of Python, because we can.
    session.interpreter = 'python3.6'

    # Set the virtualenv dirname.
    session.virtualenv_dirname = 'docs'

    # Install Sphinx and also all of the google-cloud-* packages.
    session.chdir(os.path.realpath(os.path.dirname(__file__)))
    session.install('-r', os.path.join('docs', 'requirements.txt'))

    # Build the docs!
    session.run(
        'bash', os.path.join('.', 'scripts', 'update_docs.sh'))
