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

import sys
import threading

__all__ = ['RuntimeContext']


class _RuntimeContext(object):
    @classmethod
    def clear(cls):
        raise NotImplementedError  # pragma: NO COVER

    @classmethod
    def register_slot(cls, name, default=None):
        raise NotImplementedError  # pragma: NO COVER

    def apply(self, snapshot):
        for name in snapshot:
            setattr(self, name, snapshot[name])

    def snapshot(self):
        return dict((n, self._slots[n].get()) for n in self._slots.keys())

    def __repr__(self):
        return ('{}({})'.format(type(self).__name__, self.snapshot()))

    def __getattr__(self, name):
        if name not in self._slots:
            raise AttributeError('{} is not a registered context slot'
                                 .format(name))
        slot = self._slots[name]
        return slot.get()

    def __setattr__(self, name, value):
        if name not in self._slots:
            raise AttributeError('{} is not a registered context slot'
                                 .format(name))
        slot = self._slots[name]
        slot.set(value)

    def with_current_context(self, func):
        caller_context = self.snapshot()

        def call_with_current_context(*args, **kwargs):
            try:
                backup_context = self.snapshot()
                self.apply(caller_context)
                return func(*args, **kwargs)
            finally:
                self.apply(backup_context)

        return call_with_current_context


class _ThreadLocalRuntimeContext(_RuntimeContext):
    _lock = threading.Lock()
    _slots = {}

    class Slot(object):
        _thread_local = threading.local()

        def __init__(self, name, default):
            self.name = name
            self.default = default if callable(default) else (lambda: default)

        def clear(self):
            setattr(self._thread_local, self.name, self.default())

        def get(self):
            try:
                return getattr(self._thread_local, self.name)
            except AttributeError:
                value = self.default()
                self.set(value)
                return value

        def set(self, value):
            setattr(self._thread_local, self.name, value)

    @classmethod
    def clear(cls):
        with cls._lock:
            for name in cls._slots:
                slot = cls._slots[name]
                slot.clear()

    @classmethod
    def register_slot(cls, name, default=None):
        with cls._lock:
            if name in cls._slots:
                raise ValueError('slot {} already registered'.format(name))
            cls._slots[name] = cls.Slot(name, default)


class _AsyncRuntimeContext(_RuntimeContext):
    _lock = threading.Lock()
    _slots = {}

    class Slot(object):
        def __init__(self, name, default):
            import contextvars
            self.name = name
            self.contextvar = contextvars.ContextVar(name)
            self.default = default if callable(default) else (lambda: default)

        def clear(self):
            self.contextvar.set(self.default())

        def get(self):
            try:
                return self.contextvar.get()
            except LookupError:
                value = self.default()
                self.set(value)
                return value

        def set(self, value):
            self.contextvar.set(value)

    @classmethod
    def clear(cls):
        with cls._lock:
            for name in cls._slots:
                slot = cls._slots[name]
                slot.clear()

    @classmethod
    def register_slot(cls, name, default=None):
        with cls._lock:
            if name in cls._slots:
                raise ValueError('slot {} already registered'.format(name))
            cls._slots[name] = cls.Slot(name, default)


RuntimeContext = _ThreadLocalRuntimeContext()

if sys.version_info >= (3, 7):
    RuntimeContext = _AsyncRuntimeContext()
