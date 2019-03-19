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
    def register_slot(cls, name, default = None):
        raise NotImplementedError  # pragma: NO COVER

    def __repr__(self):
        return repr(self._slots)

class _TlsRuntimeContext(_RuntimeContext):
    _lock = threading.Lock()
    _slots = {}
    _tls = threading.local()

    class Slot(object):
        def __init__(self, name, default):
            self.name = name
            self.default = default

    @classmethod
    def clear(cls):
        with cls._lock:
            for name in cls._slots:
                slot = self._slots[name]
                setattr(cls._tls, name, slot.default)

    @classmethod
    def register_slot(cls, name, default = None):
        with cls._lock:
            if name in cls._slots:
                raise ValueError('slot {} already registered'.format(name))
            cls._slots[name] = cls.Slot(name, default)

    def __init__(self):
        pass

    def __getattr__(self, name):
        if name in self._slots:
            slot = self._slots[name]
            return getattr(self._tls, name, slot.default)
        raise AttributeError('{} is not a registered context slot'.format(name))

    def __setattr__(self, name, value):
        if name in self._slots:
            return setattr(self._tls, name, value)
        raise AttributeError('{} is not a registered context slot'.format(name))

class _AsyncRuntimeContext(_RuntimeContext):
    _lock = threading.Lock()
    _slots = {}

    class Slot(object):
        def __init__(self, name, default):
            import contextvars
            self.name = name
            self.contextvar = contextvars.ContextVar(name)
            self.default = default

    @classmethod
    def clear(cls):
        with cls._lock:
            for name in cls._slots:
                slot = cls._slots[name]
                slot.contextvar.set(slot.default)

    @classmethod
    def register_slot(cls, name, default = None):
        with cls._lock:
            if name in cls._slots:
                raise ValueError('slot {} already registered'.format(name))
            cls._slots[name] = cls.Slot(name, default)

    def __init__(self):
        pass

    def __getattr__(self, name):
        if name in self._slots:
            slot = self._slots[name]
            return slot.contextvar.get(slot.default)
        raise AttributeError('{} is not a registered context slot'.format(name))

    def __setattr__(self, name, value):
        if name in self._slots:
            slot = self._slots[name]
            return slot.contextvar.set(value)
        raise AttributeError('{} is not a registered context slot'.format(name))

RuntimeContext = _TlsRuntimeContext()

if sys.version_info >= (3, 7):
    RuntimeContext = _AsyncRuntimeContext()
