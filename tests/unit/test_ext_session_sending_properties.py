# Copyright 2019-2023 Bloomberg Finance L.P.
# SPDX-License-Identifier: Apache-2.0
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

import pytest

from blazingmq import CompressionAlgorithmType
from blazingmq._ext import COMPRESSION_ALGO_FROM_PY_MAPPING as compression_map
from blazingmq._ext import Session

from .support import BINARY
from .support import BOOL
from .support import CHAR
from .support import INT32
from .support import INT64
from .support import QUEUE_NAME
from .support import SHORT
from .support import STRING
from .support import dummy_callback
from .support import sdk_mock


def test_post_with_non_dict_properties():
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, post=0, stop=None)
    session = Session(dummy_callback, _mock=mock)
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )
    payload = b"Some_message"

    # WHEN
    with pytest.raises(Exception) as exc:
        session.post(QUEUE_NAME, payload, "")

    # THEN
    assert exc.type is ValueError
    assert exc.match("'properties' is not a dictionary.")


def test_put_queue_single_message_with_valid_properties():
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, post=0, stop=None)
    session = Session(dummy_callback, _mock=mock)
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )
    payload = b"Some_message"

    # WHEN
    session.post(
        QUEUE_NAME,
        payload,
        properties={
            b"a_char": (b"a", CHAR),
            b"a_string": (b"af\xc3\xa4ae", STRING),
            b"a_binary": (b"ab\0\xc3\0", BINARY),
            b"an_int16": (12345, SHORT),
            b"an_int32": (31254, INT32),
            b"an_int64": (54321, INT64),
        },
    )

    # THEN
    mock.post.assert_called_once_with(
        payload=payload,
        queue_uri=QUEUE_NAME,
        properties=(
            {
                "a_char": b"a",
                "a_string": "af\xe4ae",
                "a_binary": b"ab\0\xc3\0",
                "an_int16": 12345,
                "an_int32": 31254,
                "an_int64": 54321,
            },
            {
                "a_char": CHAR,
                "a_string": STRING,
                "a_binary": BINARY,
                "an_int16": SHORT,
                "an_int32": INT32,
                "an_int64": INT64,
            },
        ),
        compression_algorithm_type=compression_map.get(CompressionAlgorithmType.NONE),
    )


@pytest.mark.parametrize(
    "properties, expected_type",
    [
        ({b"test": (True, CHAR)}, "bool"),
        ({b"test": ("A", STRING)}, "str"),
        ({b"test": ("A", CHAR)}, "str"),
        ({b"test": ("A", BINARY)}, "str"),
        ({b"test2": (1, STRING)}, "int"),
        ({b"test3": (1, BINARY)}, "int"),
        ({b"test4": (1, BOOL)}, "int"),
        ({b"test4": (b"", BOOL)}, "bytes"),
    ],
)
def test_post_with_invalid_types_properties(properties, expected_type):
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, post=0, stop=None)
    session = Session(dummy_callback, _mock=mock)
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )
    payload = b"Some_message"

    # WHEN
    property_name = list(properties.keys())[0].decode("ascii")
    with pytest.raises(Exception) as exc:
        session.post(QUEUE_NAME, payload, properties)

    # THEN
    assert exc.type is TypeError
    assert exc.match(
        "'%s' value is of the incorrect type, '%s' provided"
        % (property_name, expected_type)
    )


@pytest.mark.parametrize(
    "value",
    [b"", b"fe"],
)
def test_invalid_values_for_char_property(value):
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, post=0, stop=None)
    session = Session(dummy_callback, _mock=mock)
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )
    payload = b"Some_message"
    num_bytes = len(value)

    # WHEN
    with pytest.raises(Exception) as exc:
        session.post(QUEUE_NAME, payload, {b"test": (value, CHAR)})

    # THEN
    assert exc.type is TypeError
    assert exc.match(
        "'test' value does not have exactly 1 byte, %s bytes provided" % num_bytes
    )


@pytest.mark.parametrize(
    "properties, expected",
    [
        ({b"test1": (b"\xc3\xa4", STRING)}, ({"test1": "\xe4"}, {"test1": STRING})),
        (
            {b"test1": (b"\xc3\xa4", BINARY)},
            ({"test1": b"\xc3\xa4"}, {"test1": BINARY}),
        ),
        ({b"a_bool": (True, BOOL)}, ({"a_bool": True}, {"a_bool": BOOL})),
        ({b"a_char": (b"\0", CHAR)}, ({"a_char": b"\0"}, {"a_char": CHAR})),
        ({b"an_int16": (12345, SHORT)}, ({"an_int16": 12345}, {"an_int16": SHORT})),
        ({b"an_int32": (23451, INT32)}, ({"an_int32": 23451}, {"an_int32": INT32})),
        ({b"an_int64": (54321, INT64)}, ({"an_int64": 54321}, {"an_int64": INT64})),
    ],
)
def test_post_with_compatible_properties(properties, expected):
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, post=0, stop=None)
    session = Session(dummy_callback, _mock=mock)
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )
    payload = b"Some_message"

    # WHEN
    session.post(QUEUE_NAME, payload, properties)

    # THEN
    mock.post.assert_called_once_with(
        payload=payload,
        queue_uri=QUEUE_NAME,
        properties=expected,
        compression_algorithm_type=compression_map.get(CompressionAlgorithmType.NONE),
    )


@pytest.mark.parametrize(
    "prop_type, value, exception_type, match",
    [
        (SHORT, 2**15, ValueError, "Property key value must be between"),
        (SHORT, -(2**15) - 1, ValueError, "Property key value must be between"),
        (SHORT, "", TypeError, "'key' value is of the incorrect type,"),
        (INT32, 2**31, ValueError, "Property key value must be between"),
        (INT32, -(2**31) - 1, ValueError, "Property key value must be between"),
        (INT32, "", TypeError, "'key' value is of the incorrect type,"),
        (INT64, 2**63, ValueError, "Property key value must be between"),
        (INT64, -(2**63) - 1, ValueError, "Property key value must be between"),
        (INT64, "", TypeError, "'key' value is of the incorrect type,"),
    ],
)
def test_invalid_values_for_int_property(prop_type, value, exception_type, match):
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, post=0, stop=None)
    session = Session(dummy_callback, _mock=mock)
    session.open_queue_sync(
        QUEUE_NAME,
        write=True,
        read=False,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )
    properties = {b"key": (value, prop_type)}
    data = b"Some_message"

    # WHEN
    with pytest.raises(Exception) as exc:
        session.post(QUEUE_NAME, data, properties=properties)

    # THEN
    assert exc.type is exception_type
    assert exc.match(match)


@pytest.mark.parametrize(
    "prop_type, value",
    [
        (SHORT, 2**15 - 1),
        (SHORT, -(2**15)),
        (INT32, 2**31 - 1),
        (INT32, -(2**31)),
        (INT64, 2**63 - 1),
        (INT64, -(2**63)),
        (SHORT, True),
        (SHORT, False),
        (INT32, True),
        (INT32, False),
        (INT64, True),
        (INT64, False),
    ],
)
def test_valid_values_for_int_property(prop_type, value):
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, post=0, stop=None)
    session = Session(dummy_callback, _mock=mock)
    session.open_queue_sync(
        QUEUE_NAME,
        write=True,
        read=False,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )
    properties = {b"key": (value, prop_type)}
    expected = ({"key": value}, {"key": prop_type})
    data = b"Some_message"

    # WHEN
    session.post(QUEUE_NAME, data, properties=properties)

    # THEN
    mock.post.assert_called_once_with(
        payload=data,
        queue_uri=QUEUE_NAME,
        properties=expected,
        compression_algorithm_type=compression_map.get(CompressionAlgorithmType.NONE),
    )
