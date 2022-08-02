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

import os

from setuptools import find_packages, setup

BASE_DIR = os.path.dirname(__file__)
VERSION_FILENAME = os.path.join(
    BASE_DIR, "opencensus", "common", "runtime_context", "version.py"
)
PACKAGE_INFO = {}
with open(VERSION_FILENAME) as f:
    exec(f.read(), PACKAGE_INFO)

setup(
    name='opencensus-context',
    version=PACKAGE_INFO["__version__"],  # noqa
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
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    description='OpenCensus Runtime Context',
    include_package_data=True,
    long_description=open('README.rst').read(),
    install_requires=[
        # contextvars backport for Python 3.6
        'contextvars ; python_version >= "3.6" and python_version < "3.7"',
    ],
    extras_require={},
    license='Apache-2.0',
    packages=find_packages(exclude=('examples', 'tests',)),
    namespace_packages=[],
    url='https://github.com/census-instrumentation/opencensus-python/tree/master/context/opencensus-context',  # noqa: E501
    zip_safe=False,
)
