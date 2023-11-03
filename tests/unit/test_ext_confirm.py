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

import threading

import pytest

from blazingmq import exceptions
from blazingmq._ext import Session
from blazingmq._messages import create_message

from .support import QUEUE_NAME
from .support import dummy_callback
from .support import sdk_mock


@pytest.mark.parametrize(
    "confirm_rc, confirm_error",
    [(-1, "UNKNOWN"), (-3, "NOT_CONNECTED"), (-5, "NOT_SUPPORTED"), (-8, "NOT_READY")],
)
def test_confirm_fails_with_error(confirm_rc, confirm_error):
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, confirmMessage=confirm_rc, stop=None)
    session = Session(dummy_callback, _mock=mock)
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=False,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )

    # WHEN
    with pytest.raises(Exception) as exc:
        session.confirm(
            create_message(
                b"blah",
                b"\x00\x00\x0f\x00\x07\xd9\xd1z\xd0\xe1\x8c.z\x86\xe1T",
                QUEUE_NAME,
                {},
                {},
            )
        )

    # THEN
    assert exc.type is exceptions.Error
    assert exc.match(rf"Failed to confirm message \[.+\]: {confirm_error}")


def test_confirm_with_invalid_guid():
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, confirmMessage=0, stop=None)
    session = Session(dummy_callback, _mock=mock)
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )

    # WHEN
    with pytest.raises(Exception) as exc:
        session.confirm(
            create_message(b"blah", b"\x00\x00\x0f\x00", QUEUE_NAME, {}, {})
        )

    # THEN
    assert exc.type is exceptions.Error
    assert exc.match("^Invalid GUID provided$")


def test_confirm_with_invalid_queue():
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, post=0, stop=None)
    session = Session(dummy_callback, _mock=mock)

    # WHEN
    with pytest.raises(Exception) as exc:
        session.confirm(
            create_message(
                b"blah",
                b"1000000000003039CD8101000000270F",
                QUEUE_NAME,
                {},
                {},
            )
        )

    # THEN
    assert exc.type is exceptions.Error
    assert exc.match("^Queue not opened$")


def test_confirm_successful():
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, confirmMessage=0, stop=None)
    session = Session(dummy_callback, _mock=mock)
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=False,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )
    guid = b"\x00\x00\x0f\x00\x07\xd9\xd1z\xd0\xe1\x8c.z\x86\xe1T"

    # WHEN
    session.confirm(
        create_message(
            b"blah",
            guid,
            QUEUE_NAME,
            {},
            {},
        )
    )

    # THEN
    mock.confirmMessage.assert_called_once_with(queue_uri=QUEUE_NAME, guid=guid)


def test_confirm_with_closing_queue():
    # GIVEN
    mock = sdk_mock(
        start=0, openQueueSync=0, confirmMessage=0, close_on_get=True, stop=None
    )
    session = Session(dummy_callback, _mock=mock)
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=False,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )
    guid = b"\x00\x00\x0f\x00\x07\xd9\xd1z\xd0\xe1\x8c.z\x86\xe1T"

    # WHEN
    with pytest.raises(Exception) as exc:
        session.confirm(
            create_message(
                b"blah",
                guid,
                QUEUE_NAME,
                {},
                {},
            )
        )

    # THEN
    assert exc.type is exceptions.Error
    assert exc.match("Attempting to confirm message on a closing queue.")
    assert exc.match(r"configure with 0 max unconfirmed message")
    assert exc.match("queue<%s>" % QUEUE_NAME.decode("ascii"))


def test_message_handle_can_confirm():
    # GIVEN
    guid = b"1000000000003039CD8101000000270F"
    messages = [[(b"data", guid, QUEUE_NAME, {}, {})]]
    _mock = sdk_mock(
        start=0, openQueueSync=0, confirmMessage=0, enqueue_messages=messages, stop=None
    )
    waiting = threading.Event()

    def on_message(_, msg_handle):
        msg_handle.confirm()
        waiting.set()

    session = Session(dummy_callback, on_message=on_message, _mock=_mock)

    # WHEN
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=False,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )
    waiting.wait()

    # THEN
    _mock.confirmMessage.assert_called_once_with(
        queue_uri=QUEUE_NAME,
        guid=b"\x10\x00\x00\x00\x00\x0009\xcd\x81\x01\x00\x00\x00'\x0f",
    )
