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
import shutil
import unittest

import mock

from opencensus.ext.azure.common.storage import (
    LocalFileBlob,
    LocalFileStorage,
    _now,
    _seconds,
)

TEST_FOLDER = os.path.abspath('.test.storage')


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
        blob.delete()
        with mock.patch('os.remove') as m:
            blob.delete()
            m.assert_called_once_with(os.path.join(TEST_FOLDER, 'foobar'))

    def test_get(self):
        blob = LocalFileBlob(os.path.join(TEST_FOLDER, 'foobar'))
        self.assertIsNone(blob.get())

    def test_put_without_lease(self):
        blob = LocalFileBlob(os.path.join(TEST_FOLDER, 'foobar.blob'))
        input = (1, 2, 3)
        blob.delete()
        blob.put(input)
        self.assertEqual(blob.get(), input)

    def test_put_with_lease(self):
        blob = LocalFileBlob(os.path.join(TEST_FOLDER, 'foobar.blob'))
        input = (1, 2, 3)
        blob.delete()
        blob.put(input, lease_period=0.01)
        blob.lease(0.01)
        self.assertEqual(blob.get(), input)

    def test_lease_error(self):
        blob = LocalFileBlob(os.path.join(TEST_FOLDER, 'foobar.blob'))
        blob.delete()
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
                self.assertIsNone(stor.put(input))

    def test_put_max_size(self):
        input = (1, 2, 3)
        with LocalFileStorage(os.path.join(TEST_FOLDER, 'asd')) as stor:
            size_mock = mock.Mock()
            size_mock.return_value = False
            stor._check_storage_size = size_mock
            stor.put(input)
            self.assertEqual(stor.get(), None)

    def test_check_storage_size_full(self):
        input = (1, 2, 3)
        with LocalFileStorage(os.path.join(TEST_FOLDER, 'asd2'), 1) as stor:
            stor.put(input)
            self.assertFalse(stor._check_storage_size())

    def test_check_storage_size_not_full(self):
        input = (1, 2, 3)
        with LocalFileStorage(os.path.join(TEST_FOLDER, 'asd3'), 1000) as stor:
            stor.put(input)
            self.assertTrue(stor._check_storage_size())

    def test_check_storage_size_no_files(self):
        with LocalFileStorage(os.path.join(TEST_FOLDER, 'asd3'), 1000) as stor:
            self.assertTrue(stor._check_storage_size())

    def test_check_storage_size_links(self):
        input = (1, 2, 3)
        with LocalFileStorage(os.path.join(TEST_FOLDER, 'asd4'), 1000) as stor:
            stor.put(input)
            with mock.patch('os.path.islink') as os_mock:
                os_mock.return_value = True
            self.assertTrue(stor._check_storage_size())

    def test_check_storage_size_error(self):
        input = (1, 2, 3)
        with LocalFileStorage(os.path.join(TEST_FOLDER, 'asd5'), 1) as stor:
            with mock.patch('os.path.getsize', side_effect=throw(OSError)):
                stor.put(input)
                with mock.patch('os.path.islink') as os_mock:
                    os_mock.return_value = True
                self.assertTrue(stor._check_storage_size())

    def test_check_storage_size_above_max_limit(self):
        input = (1, 2, 3)
        with LocalFileStorage(os.path.join(TEST_FOLDER, 'asd5'), 1) as stor:
            with mock.patch('os.path.getsize') as os_mock:
                os_mock.return_value = 52000000
                stor.put(input)
                with mock.patch('os.path.islink') as os_mock:
                    os_mock.return_value = True
                self.assertFalse(stor._check_storage_size())

    def test_maintenance_routine(self):
        with mock.patch('os.makedirs') as m:
            LocalFileStorage(os.path.join(TEST_FOLDER, 'baz'))
            m.assert_called_once_with(os.path.join(TEST_FOLDER, 'baz'))
        with mock.patch('os.makedirs') as m:
            m.return_value = None
            LocalFileStorage(os.path.join(TEST_FOLDER, 'baz'))
            m.assert_called_once_with(os.path.join(TEST_FOLDER, 'baz'))
        with mock.patch('os.makedirs', side_effect=throw(Exception)):
            LocalFileStorage(os.path.join(TEST_FOLDER, 'baz'))
            m.assert_called_once_with(os.path.join(TEST_FOLDER, 'baz'))
        with mock.patch('os.listdir', side_effect=throw(Exception)):
            LocalFileStorage(os.path.join(TEST_FOLDER, 'baz'))
            m.assert_called_once_with(os.path.join(TEST_FOLDER, 'baz'))
        with LocalFileStorage(os.path.join(TEST_FOLDER, 'baz')) as stor:
            with mock.patch('os.listdir', side_effect=throw(Exception)) as p:
                stor._maintenance_routine()
                stor._maintenance_routine()
                self.assertEqual(p.call_count, 2)
            patch = 'os.path.isdir'
            with mock.patch(patch, side_effect=throw(Exception)) as isdir:
                stor._maintenance_routine()
                stor._maintenance_routine()
                self.assertEqual(isdir.call_count, 2)
