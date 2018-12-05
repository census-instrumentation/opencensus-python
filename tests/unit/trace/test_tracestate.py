# Copyright 2018, OpenCensus Authors
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

import unittest

from opencensus.trace.tracestate import Tracestate
from opencensus.trace.propagation.tracestate_string_format \
    import TracestateStringFormatter

formatter = TracestateStringFormatter()


class TestTracestate(unittest.TestCase):
    def test_ctor_no_arg(self):
        state = Tracestate()
        self.assertEqual(formatter.to_string(state), '')

    def test_ctor_with_dict(self):
        state = Tracestate({'foo': '1'})
        self.assertEqual(formatter.to_string(state), 'foo=1')

    def test_cctor(self):
        state = Tracestate(formatter.from_string('foo=1,bar=2,baz=3'))
        self.assertEqual(formatter.to_string(state), 'foo=1,bar=2,baz=3')

    def test_all_allowed_chars(self):
        header = ''.join([
            # key
            ''.join(map(chr, range(0x61, 0x7A + 1))),  # lcalpha
            '0123456789',  # DIGIT
            '_',
            '-',
            '*',
            '/',
            # "="
            '=',
            # value
            ''.join(map(chr, range(0x20, 0x2B + 1))),
            ''.join(map(chr, range(0x2D, 0x3C + 1))),
            ''.join(map(chr, range(0x3E, 0x7E + 1))),
        ])
        state = formatter.from_string(header)
        self.assertEqual(formatter.to_string(state), header)

    def test_delimiter(self):
        state = formatter.from_string('foo=1, \t bar=2')
        self.assertEqual(formatter.to_string(state), 'foo=1,bar=2')

        state = formatter.from_string('foo=1,\t \tbar=2')
        self.assertEqual(formatter.to_string(state), 'foo=1,bar=2')

    def test_get(self):
        state = Tracestate({'foo': '1'})
        self.assertEqual(state['foo'], '1')

    def test_method_append(self):
        state = Tracestate()
        state.append('foo', '1')
        state.append('bar', '2')
        state.append('baz', '3')
        state.append('bar', '2')
        self.assertEqual(formatter.to_string(state), 'foo=1,baz=3,bar=2')

    def test_method_from_string(self):
        state = formatter.from_string('foo=1,bar=2,baz=3')
        self.assertEqual(formatter.to_string(state), 'foo=1,bar=2,baz=3')

        self.assertRaises(ValueError, lambda: formatter.from_string('#=#'))

    def test_method_get(self):
        state = formatter.from_string('foo=1, bar=2, baz=3')
        self.assertEqual(state.get('bar'), '2')

    def test_method_is_valid(self):
        state = Tracestate()

        # empty state not allowed
        self.assertFalse(state.is_valid())

        state['foo'] = 'x' * 256
        self.assertTrue(state.is_valid())

        # exceeds 32 elements
        for i in range(0xa0, 0xa0 + 31):
            state['%x' % (i)] = 'E'
        self.assertEqual(len(state), 32)
        self.assertTrue(state.is_valid())
        state['ff'] = 'E'
        self.assertFalse(state.is_valid())

    def test_method_prepend(self):
        state = Tracestate()
        state.prepend('foo', '1')
        state.prepend('baz', '3')
        state.prepend('bar', '2')
        self.assertEqual(formatter.to_string(state), 'bar=2,baz=3,foo=1')

        # modified key-value pair MUST be moved to the beginning of the list
        state.prepend('foo', '1')
        self.assertEqual(formatter.to_string(state), 'foo=1,bar=2,baz=3')

    def test_pop(self):
        state = formatter.from_string('foo=1,bar=2,baz=3')
        state.popitem()
        self.assertEqual(formatter.to_string(state), 'foo=1,bar=2')
        state.popitem()
        self.assertEqual(formatter.to_string(state), 'foo=1')
        state.popitem()
        self.assertEqual(formatter.to_string(state), '')
        # raise KeyError exception while trying to pop from nothing
        self.assertRaises(KeyError, lambda: state.popitem())

    def test_set(self):
        state = Tracestate({'bar': '0'})
        state['foo'] = '1'
        state['bar'] = '2'
        state['baz'] = '3'
        self.assertEqual(formatter.to_string(state), 'bar=2,foo=1,baz=3')

        # key SHOULD be string
        self.assertRaises(ValueError, lambda: state.__setitem__(123, 'abc'))
        # value SHOULD NOT be empty string
        self.assertRaises(ValueError, lambda: state.__setitem__('', 'abc'))
        # key SHOULD start with a letter
        self.assertRaises(ValueError, lambda: state.__setitem__('123', 'abc'))
        # key SHOULD NOT have uppercase
        self.assertRaises(ValueError, lambda: state.__setitem__('FOO', 'abc'))

        # value SHOULD be string
        self.assertRaises(ValueError, lambda: state.__setitem__('foo', 123))
        # value SHOULD NOT be empty string
        self.assertRaises(ValueError, lambda: state.__setitem__('foo', ''))

        state['foo'] = 'x' * 256
        # throw if value exceeds 256 bytes
        self.assertRaises(ValueError,
                          lambda: state.__setitem__('foo', 'x' * 257))
