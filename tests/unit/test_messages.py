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

import weakref

import pytest

import blazingmq
from blazingmq import _callbacks
from blazingmq._messages import create_ack
from blazingmq._messages import create_message
from blazingmq._messages import create_message_handle

from .support import QUEUE_NAME
from .support import mock


def test_create_message():
    # GIVEN / WHEN
    data = b"bytes"
    guid = b"guid"
    queue_uri = QUEUE_NAME.decode("utf-8")
    properties = {"foo": "m"}
    property_types = {"foo": blazingmq.PropertyType.CHAR}
    m = create_message(data, guid, queue_uri, properties, property_types)

    # THEN
    assert m.data == data
    assert m.guid == guid
    assert m.queue_uri == queue_uri
    assert m.properties["foo"] == properties["foo"]
    assert m.property_types["foo"] == property_types["foo"]


def test_construct_message():
    # GIVEN
    # WHEN
    with pytest.raises(Exception) as exc:
        blazingmq.Message()

    # THEN
    assert exc.type is blazingmq.Error
    assert exc.match("^The Message class does not have a public constructor.")


def test_message_repr():
    # GIVEN / WHEN
    data = b"bytes"
    guid = b"\x00\x00\x0f\x00\x07\xd9\xd1z\xd0\xe1\x8c.z\x86\xe1T"
    queue_uri = "bmq://foo/bar"
    properties = {"foo": "m"}
    property_types = {"foo": blazingmq.PropertyType.CHAR}
    m = create_message(data, guid, queue_uri, properties, property_types)

    # THEN
    assert repr(m) == "<Message[00000F0007D9D17AD0E18C2E7A86E154] for bmq://foo/bar>"


def test_create_ack():
    # GIVEN / WHEN
    guid = b"guid"
    status = blazingmq.AckStatus.SUCCESS
    queue_uri = "bmq://foo/bar"
    ack = create_ack(guid, status, "SUCCESS", queue_uri)

    # THEN
    assert ack.guid == guid
    assert ack.status == status
    assert ack.queue_uri == queue_uri


def test_construct_ack():
    # GIVEN
    # WHEN
    with pytest.raises(Exception) as exc:
        blazingmq.Ack()

    # THEN
    assert exc.type is blazingmq.Error
    assert exc.match("^The Ack class does not have a public constructor.")


def test_ack_repr():
    # GIVEN / WHEN
    guid = b"\x00\x00\x0f\x00\x07\xd9\xd1z\xd0\xe1\x8c.z\x86\xe1T"
    queue_uri = "bmq://foo/bar"
    status = blazingmq.AckStatus.TIMEOUT
    m = create_ack(guid, status, "TIMEOUT", queue_uri)

    # THEN
    assert (
        repr(m) == "<Ack[00000F0007D9D17AD0E18C2E7A86E154] TIMEOUT for bmq://foo/bar>"
    )


def test_ack_repr_uses_description():
    # GIVEN / WHEN
    guid = b"\x00\x00\x0f\x00\x07\xd9\xd1z\xd0\xe1\x8c.z\x86\xe1T"
    queue_uri = "bmq://foo/bar"
    status = blazingmq.AckStatus.SUCCESS
    m = create_ack(guid, status, "TIMEOUT", queue_uri)

    # THEN
    assert (
        repr(m) == "<Ack[00000F0007D9D17AD0E18C2E7A86E154] TIMEOUT for bmq://foo/bar>"
    )


def test_ack_status_repr():
    # GIVEN / WHEN / THEN
    assert repr(blazingmq.AckStatus.CANCELED) == "<AckStatus.CANCELED>"


def test_type_property_repr():
    # GIVEN / WHEN / THEN
    assert repr(blazingmq.PropertyType.CHAR) == "<PropertyType.CHAR>"


def test_type_compression_algorithm_repr():
    # GIVEN / WHEN / THEN
    assert (
        repr(blazingmq.CompressionAlgorithmType.NONE)
        == "<CompressionAlgorithmType.NONE>"
    )
    assert (
        repr(blazingmq.CompressionAlgorithmType.ZLIB)
        == "<CompressionAlgorithmType.ZLIB>"
    )


def test_message_received_in_callback():
    # GIVEN
    spy = mock.MagicMock()

    class FakeSession:
        pass

    ext_session = FakeSession()
    raw = (b"data", b"guid", b"queue_uri", ({}, {}))

    # WHEN
    _callbacks.on_message(spy, weakref.ref(ext_session), {}, [raw])

    # THEN
    spy.assert_called_once()
    args, kwargs = spy.call_args
    assert not kwargs
    (msg, msg_handle) = args
    assert isinstance(msg, blazingmq.Message)
    assert isinstance(msg_handle, blazingmq.MessageHandle)
    assert msg.data == raw[0]
    assert msg.guid == raw[1]
    assert msg.queue_uri == raw[2].decode("utf-8")


def test_construct_message_handle():
    # GIVEN
    # WHEN
    with pytest.raises(Exception) as exc:
        blazingmq.MessageHandle()

    # THEN
    assert exc.type is blazingmq.Error
    assert exc.match("^The MessageHandle class does not have a public constructor.")


def test_message_repr_context():
    guid = bytes.fromhex("00000F0007D9D17AD0E18C2E7A86E154")
    queue_uri = "bmq://foo/bar"
    message = create_message(b"bytes", guid, queue_uri, {}, {})
    ext_session = object()
    msg_handle = create_message_handle(message, ext_session)

    # THEN
    expected = "<MessageHandle[00000F0007D9D17AD0E18C2E7A86E154] for bmq://foo/bar>"
    assert repr(msg_handle) == expected


def test_call_confirm_on_message_handle():
    # GIVEN / WHEN
    message = create_message(b"bytes", b"guid", QUEUE_NAME.decode("utf-8"), {}, {})
    ext_session = mock.MagicMock()
    ext_session.mock_add_spec(["confirm"])
    msg_handle = create_message_handle(message, ext_session)

    # WHEN
    msg_handle.confirm()

    # THEN
    ext_session.confirm.assert_called_with(message)
