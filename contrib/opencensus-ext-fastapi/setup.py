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

from setuptools import find_packages, setup

from version import __version__

setup(
    name='opencensus-ext-fastapi-dev',
    version=__version__,  # noqa
    author='Opensource contribution',
    author_email='basmaelsaify@gmail.com',
    classifiers=[
        'Intended Audience :: Developers',
        'Development Status :: 1 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
    ],
    description='OpenCensus FastAPI Integration',
    include_package_data=True,
    long_description=open('README.rst').read(),
    install_requires=[
        'fastapi >= 0.61.0, < 0.63.0',
        'opencensus >= 0.8.dev0, < 1.0.0',
    ],
    extras_require={},
    license='Apache-2.0',
    packages=find_packages(exclude=('examples', 'tests',)),
    namespace_packages=[],
    url='https://github.com/Basma-Elsaify/opencensus-python/tree/master/contrib/opencensus-ext-fastapi',  # noqa: E501
    zip_safe=False,
)
