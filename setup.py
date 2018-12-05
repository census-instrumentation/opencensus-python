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
"""A setup module for Open Source Census Instrumentation Library"""

from setuptools import find_packages
from setuptools import setup

extras = {
    "stackdriver": ['google-cloud-trace>=0.19.0, <0.20'],
    "prometheus_client": ['prometheus_client==0.3.1']
}

install_requires = [
    'google-api-core >= 1.0.0, < 2.0.0',
]

exec(open("opencensus/__version__.py").read())
setup(
    name='opencensus',
    version=__version__,  # noqa
    author='OpenCensus Authors',
    author_email='census-developers@googlegroups.com',
    classifiers=[
        'Intended Audience :: Developers',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    description='A stats collection and distributed tracing framework',
    include_package_data=True,
    long_description=open('README.rst').read(),
    install_requires=install_requires,
    extras_require=extras,
    license='Apache-2.0',
    packages=find_packages(),
    namespace_packages=[],
    url='https://github.com/census-instrumentation/opencensus-python')
