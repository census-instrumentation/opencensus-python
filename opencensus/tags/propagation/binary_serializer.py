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

import binascii
import collections
import logging
import struct
import sys
from google.protobuf.internal.encoder import _VarintEncoder
from google.protobuf.internal.encoder import _VarintBytes
from google.protobuf.internal.encoder import TagBytes
from google.protobuf.internal.decoder import _DecodeVarint

from opencensus.tags import tag_map as tag_map_module
from opencensus.tags.tag_key import TagKey
from opencensus.tags.tag_value import TagValue

# Used for decoding hex bytes to hex string.
UTF8 = 'utf-8'

VERSION_ID = 0
TAG_FIELD_ID = 0
TAG_MAP_SERIALIZED_SIZE_LIMIT = 8192

# See: https://docs.python.org/3/library/struct.html#format-characters
BIG_ENDIAN = '>'
CHAR_ARRAY_FORMAT = 's'
UNSIGNED_CHAR = 'B'
UNSIGNED_LONG_LONG = 'Q'

# Adding big endian indicator at the beginning to avoid auto padding. This is
# for ensuring the length of binary is not changed when propagating.
BINARY_FORMAT = '{big_endian}{version_id}' \
                '{tag_field_id}' \
                '{tag_key_len}{tag_key}' \
                '{tag_val_len}{tag_val}' \
    .format(big_endian=BIG_ENDIAN,
            version_id=UNSIGNED_CHAR,
            tag_field_id=UNSIGNED_CHAR,
            tag_key_len=UNSIGNED_CHAR,
            tag_key='{}{}'.format(tag_key_len, CHAR_ARRAY_FORMAT),
            tag_val_len=UNSIGNED_CHAR,
            tag_val='{}{}'.format(tag_val_len, CHAR_ARRAY_FORMAT))

Header = collections.namedtuple(
    'Header',
    'version_id '
    'tag_field_id '
    'tag_key_len '
    'tag_key '
    'tag_val_len '
    'tal_val'
)


class BinarySerializer(object):
    def from_header(self, binary):
        if binary is None:
            return tag_map_module.TagMap(from_header=False)
        try:
            data = Header._make(struct.unpack(BINARY_FORMAT, binary))
        except struct.error:
            logging.warning(
                'Cannot parse the incoming binary data {}, '
                'wrong format. Total bytes length should be {}.'.format(
                    binary, TAG_MAP_SERIALIZED_SIZE_LIMIT
                )
            )
            return tag_map_module.TagMap(from_header=False)
        version_id = data.version_id
        buffer = memoryview(bytearray(binary, 'UTF-8'))
        total_chars = 0
        if 0 < version_id < VERSION_ID:
            tags = {}
            length = len(buffer)
            i = 0
            while i < length:
                if buffer[i] is not None:
                    tag_id = buffer.__getitem__(TAG_FIELD_ID)
                    if tag_id == TAG_FIELD_ID:
                        key = _DecodeVarint(buffer, i)
                        val = {key: _DecodeVarint(buffer, i)}
                        total_chars += len(key)
                        total_chars += len(val)
                        tags[key] = val
                i += 1
            tag_map = tag_map_module.TagMap(tags=tags, from_header=True)
            return tag_map

    def to_header(self, tag_context):
        total_chars = 0
        for tag in tag_context:
            total_chars += len(tag.key)
            total_chars += len(tag.value)
            if total_chars <= TAG_MAP_SERIALIZED_SIZE_LIMIT:
                temp_tag_key_len = len(tag.key)
                tag_key_len = _VarintBytes(temp_tag_key_len)
                temp_tag_val_len = len(tag.value)
                tag_val_len = _VarintBytes(temp_tag_val_len)

                return struct.pack(
                    BINARY_FORMAT,
                    VERSION_ID,
                    TAG_FIELD_ID,
                    tag_key_len,
                    binascii.unhexlify(tag.key),
                    tag_val_len,
                    binascii.unhexlify(tag.value))
