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


class Object(dict):
    def __init__(self, *args, **kwargs):
        super(Object, self).__init__(*args, **kwargs)
        for key in kwargs:
            self[key] = kwargs[key]

    def __repr__(self):
        tmp = {}
        while True:
            for item in self.items():
                if item[0] not in tmp:
                    tmp[item[0]] = item[1]
            if self.prototype == self:
                break
            self = self.prototype
        return repr(tmp)

    def __setattr__(self, name, value):
        self[name] = value

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as ex:
            raise AttributeError("'{}' object has no attribute {}".format(
                type(self).__name__,
                ex,
            ))

    def __getitem__(self, key):
        if self.prototype is self:
            return super(Object, self).__getitem__(key)
        if key in self:
            return super(Object, self).__getitem__(key)
        return self.prototype[key]


Object.prototype = Object()


class Data(Object):
    prototype = Object(
        baseData=None,
        baseType=None,
    )

    def __init__(self, *args, **kwargs):
        super(Data, self).__init__(*args, **kwargs)
        self.baseData = self.baseData
        self.baseType = self.baseType


class Envelope(Object):
    prototype = Object(
        ver=1,
        name='',
        time='',
        sampleRate=None,
        seq=None,
        iKey=None,
        flags=None,
        tags=None,
        data=None,
    )

    def __init__(self, *args, **kwargs):
        super(Envelope, self).__init__(*args, **kwargs)
        self.name = self.name
        self.time = self.time


class Event(Object):
    prototype = Object(
        ver=2,
        name='',
        properties=None,
        measurements=None,
    )

    def __init__(self, *args, **kwargs):
        super(Event, self).__init__(*args, **kwargs)
        self.ver = self.ver
        self.name = self.name


class Message(Object):
    prototype = Object(
        ver=2,
        message='',
        severityLevel=None,
        properties=None,
        measurements=None,
    )

    def __init__(self, *args, **kwargs):
        super(Message, self).__init__(*args, **kwargs)
        self.ver = self.ver
        self.message = self.message


class RemoteDependency(Object):
    prototype = Object(
        ver=2,
        name='',
        id='',
        resultCode='',
        duration='',
        success=True,
        data=None,
        type=None,
        target=None,
        properties=None,
        measurements=None,
    )

    def __init__(self, *args, **kwargs):
        super(RemoteDependency, self).__init__(*args, **kwargs)
        self.ver = self.ver
        self.name = self.name
        self.resultCode = self.resultCode
        self.duration = self.duration


class Request(Object):
    prototype = Object(
        ver=2,
        id='',
        duration='',
        responseCode='',
        success=True,
        source=None,
        name=None,
        url=None,
        properties=None,
        measurements=None,
    )

    def __init__(self, *args, **kwargs):
        super(Request, self).__init__(*args, **kwargs)
        self.ver = self.ver
        self.id = self.id
        self.duration = self.duration
        self.responseCode = self.responseCode
        self.success = self.success
