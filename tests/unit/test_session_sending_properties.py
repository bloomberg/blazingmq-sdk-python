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

from blazingmq import Error
from blazingmq import PropertyType
import pytest

from .support import BINARY
from .support import BOOL
from .support import CHAR
from .support import INT32
from .support import INT64
from .support import SHORT
from .support import STRING
from .support import make_session


def test_session_post_with_properties(ext):
    # GIVEN
    ext.mock_add_spec(["post"])
    session = make_session()
    properties = {"a": "b"}
    property_type_overrides = {}
    merged = {b"a": (b"b", STRING)}

    # WHEN
    session.post(
        "queue_uri",
        b"data",
        properties=properties,
        property_type_overrides=property_type_overrides,
    )

    # THEN
    ext.post.assert_called_once_with(
        b"queue_uri",
        b"data",
        properties=merged,
        on_ack=None,
    )


def test_session_post_property_default_types(ext):
    # GIVEN
    ext.mock_add_spec(["post"])
    session = make_session()
    properties = {"Bool": True, "Int": 65536, "Str": "\xE4"}
    merged = {
        b"Bool": (True, BOOL),
        b"Int": (65536, INT64),
        b"Str": (b"\xC3\xA4", STRING),
    }

    # WHEN
    session.post(
        "queue_uri",
        b"data",
        properties=properties,
    )

    # THEN
    ext.post.assert_called_once_with(
        b"queue_uri",
        b"data",
        properties=merged,
        on_ack=None,
    )


def test_session_post_property_default_for_byte_string_is_binary_in_3(ext):
    # GIVEN
    ext.mock_add_spec(["post"])
    session = make_session()
    properties = {"Bytes": b"a\0b"}
    merged = {b"Bytes": (b"a\0b", BINARY)}

    # WHEN
    session.post("queue_uri", b"data", properties=properties)

    # THEN
    ext.post.assert_called_once_with(
        b"queue_uri",
        b"data",
        properties=merged,
        on_ack=None,
    )


def test_session_post_property_type_overrides(ext):
    # GIVEN
    ext.mock_add_spec(["post"])
    session = make_session()
    properties = {"Bool": True, "Int": 65536, "Bytes": b"a"}
    property_type_overrides = {
        "Bool": PropertyType.SHORT,
        "Int": PropertyType.INT32,
        "Bytes": PropertyType.CHAR,
    }
    merged = {
        b"Bool": (1, SHORT),
        b"Int": (65536, INT32),
        b"Bytes": (b"a", CHAR),
    }

    # WHEN
    session.post(
        "queue_uri",
        b"data",
        properties=properties,
        property_type_overrides=property_type_overrides,
    )

    # THEN
    ext.post.assert_called_once_with(
        b"queue_uri",
        b"data",
        properties=merged,
        on_ack=None,
    )


def test_session_post_property_type_overrides_mixed_bytes_unicode(ext):
    # GIVEN
    ext.mock_add_spec(["post"])
    session = make_session()
    properties = {"Bool": True, "Int": 65536, b"Bytes": b"a"}
    property_type_overrides = {
        b"Bool": PropertyType.SHORT,
        b"Int": PropertyType.INT32,
        "Bytes": PropertyType.CHAR,
    }
    merged = {
        b"Bool": (1, SHORT),
        b"Int": (65536, INT32),
        b"Bytes": (b"a", CHAR),
    }

    # WHEN
    session.post(
        "queue_uri",
        b"data",
        properties=properties,
        property_type_overrides=property_type_overrides,
    )

    # THEN
    ext.post.assert_called_once_with(
        b"queue_uri",
        b"data",
        properties=merged,
        on_ack=None,
    )


def test_session_post_property_type_with_invalid_property_name_type(ext):
    # GIVEN
    ext.mock_add_spec(["post"])
    session = make_session()
    properties = {True: True}
    property_type_overrides = {
        True: PropertyType.SHORT,
    }

    # WHEN
    with pytest.raises(Exception) as exc:
        session.post(
            "queue_uri",
            b"data",
            properties=properties,
            property_type_overrides=property_type_overrides,
        )

    # THEN
    assert exc.type is TypeError
    assert exc.match("not expecting type")


def test_session_post_extra_property_type_overrides(ext):
    # GIVEN
    ext.mock_add_spec(["post"])
    session = make_session()
    properties = {"Bool": True}
    property_type_overrides = {"Bool": PropertyType.SHORT, "Int": PropertyType.INT32}

    # WHEN
    with pytest.raises(Exception) as exc:
        session.post(
            "queue_uri",
            b"data",
            properties=properties,
            property_type_overrides=property_type_overrides,
        )

    # THEN
    assert exc.type is Error
    assert exc.match("Received override for non-existent property 'Int'")


def test_session_post_property_type_overrides_without_properties(ext):
    # GIVEN
    ext.mock_add_spec(["post"])
    session = make_session()
    property_type_overrides = {"Bool": PropertyType.SHORT}

    # WHEN
    with pytest.raises(Exception) as exc:
        session.post(
            "queue_uri",
            b"data",
            property_type_overrides=property_type_overrides,
        )

    # THEN
    assert exc.type is Error
    assert exc.match("Received override for non-existent property 'Bool'")


def test_session_post_unsupported_property_value(ext):
    # GIVEN
    ext.mock_add_spec(["post"])
    session = make_session()
    properties = {"Float": 42.0}

    # WHEN
    with pytest.raises(Exception) as exc:
        session.post(
            "queue_uri",
            b"data",
            properties=properties,
        )

    # THEN
    assert exc.type is Error
    assert exc.match("Property values of type 'float' are not supported")
