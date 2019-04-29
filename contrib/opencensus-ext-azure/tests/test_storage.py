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

import mock
import os
import shutil
import unittest

from opencensus.ext.azure.common.storage import _now
from opencensus.ext.azure.common.storage import _seconds
from opencensus.ext.azure.common.storage import LocalFileBlob
from opencensus.ext.azure.common.storage import LocalFileStorage

TEST_FOLDER = os.path.abspath('.test')


def setUpModule():
    os.makedirs(TEST_FOLDER)


def tearDownModule():
    shutil.rmtree(TEST_FOLDER)


def throw(exc_type, *args, **kwargs):
    def func(*_args, **_kwargs):
        raise exc_type(*args, **kwargs)
    return func


class TestLocalFileBlob(unittest.TestCase):
    def test_delete(self):
        blob = LocalFileBlob(os.path.join(TEST_FOLDER, 'foobar'))
        blob.delete(silent=True)
        self.assertRaises(Exception, lambda: blob.delete())
        self.assertRaises(Exception, lambda: blob.delete(silent=False))

    def test_get(self):
        blob = LocalFileBlob(os.path.join(TEST_FOLDER, 'foobar'))
        self.assertIsNone(blob.get(silent=True))
        self.assertRaises(Exception, lambda: blob.get())
        self.assertRaises(Exception, lambda: blob.get(silent=False))

    def test_put_error(self):
        blob = LocalFileBlob(os.path.join(TEST_FOLDER, 'foobar'))
        with mock.patch('os.rename', side_effect=throw(Exception)):
            self.assertRaises(Exception, lambda: blob.put([1, 2, 3]))

    def test_put_without_lease(self):
        blob = LocalFileBlob(os.path.join(TEST_FOLDER, 'foobar.blob'))
        input = (1, 2, 3)
        blob.delete(silent=True)
        blob.put(input)
        self.assertEqual(blob.get(), input)

    def test_put_with_lease(self):
        blob = LocalFileBlob(os.path.join(TEST_FOLDER, 'foobar.blob'))
        input = (1, 2, 3)
        blob.delete(silent=True)
        blob.put(input, lease_period=0.01)
        blob.lease(0.01)
        self.assertEqual(blob.get(), input)

    def test_lease_error(self):
        blob = LocalFileBlob(os.path.join(TEST_FOLDER, 'foobar.blob'))
        blob.delete(silent=True)
        self.assertEqual(blob.lease(0.01), None)


class TestLocalFileStorage(unittest.TestCase):
    def test_get_nothing(self):
        with LocalFileStorage(os.path.join(TEST_FOLDER, 'test', 'a')) as stor:
            pass
        with LocalFileStorage(os.path.join(TEST_FOLDER, 'test')) as stor:
            self.assertIsNone(stor.get())

    def test_get(self):
        now = _now()
        with LocalFileStorage(os.path.join(TEST_FOLDER, 'foo')) as stor:
            stor.put((1, 2, 3), lease_period=10)
            with mock.patch('opencensus.ext.azure.common.storage._now') as m:
                m.return_value = now - _seconds(30 * 24 * 60 * 60)
                stor.put((1, 2, 3))
                stor.put((1, 2, 3), lease_period=10)
                with mock.patch('os.rename'):
                    stor.put((1, 2, 3))
            with mock.patch('os.rename'):
                stor.put((1, 2, 3))
            with mock.patch('os.remove', side_effect=throw(Exception)):
                with mock.patch('os.rename', side_effect=throw(Exception)):
                    self.assertIsNone(stor.get())
            self.assertIsNone(stor.get())

    def test_put(self):
        input = (1, 2, 3)
        with LocalFileStorage(os.path.join(TEST_FOLDER, 'bar')) as stor:
            stor.put(input)
            self.assertEqual(stor.get().get(), input)
        with LocalFileStorage(os.path.join(TEST_FOLDER, 'bar')) as stor:
            self.assertEqual(stor.get().get(), input)
            with mock.patch('os.rename', side_effect=throw(Exception)):
                self.assertIsNone(stor.put(input, silent=True))
                self.assertRaises(Exception, lambda: stor.put(input))

    def test_maintanence_routine(self):
        with mock.patch('os.makedirs') as m:
            m.return_value = None
            self.assertRaises(
                Exception,
                lambda: LocalFileStorage(os.path.join(TEST_FOLDER, 'baz')),
            )
        with mock.patch('os.makedirs', side_effect=throw(Exception)):
            self.assertRaises(
                Exception,
                lambda: LocalFileStorage(os.path.join(TEST_FOLDER, 'baz')),
            )
        with mock.patch('os.listdir', side_effect=throw(Exception)):
            self.assertRaises(
                Exception,
                lambda: LocalFileStorage(os.path.join(TEST_FOLDER, 'baz')),
            )
        with LocalFileStorage(os.path.join(TEST_FOLDER, 'baz')) as stor:
            with mock.patch('os.listdir', side_effect=throw(Exception)):
                stor._maintenance_routine(silent=True)
                self.assertRaises(
                    Exception,
                    lambda: stor._maintenance_routine(),
                )
            with mock.patch('os.path.isdir', side_effect=throw(Exception)):
                stor._maintenance_routine(silent=True)
                self.assertRaises(
                    Exception,
                    lambda: stor._maintenance_routine(),
                )
