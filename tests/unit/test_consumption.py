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

import queue

from blazingmq._enums import PropertyType
from blazingmq._ext import Session
from blazingmq._messages import AckStatus
from blazingmq._messages import pretty_hex
import pytest

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


def test_multiple_message_consumption():
    # GIVEN
    messages = [
        [
            (
                b"payload1",
                b"1000000000003039CD8101000000270F",
                QUEUE_NAME + b"1",
                {},
            ),
            (
                b"payload2",
                b"2000000000003039CD8101000000270F",
                QUEUE_NAME + b"1",
                {},
            ),
        ],
        [
            (
                b"payload3",
                b"3000000000003039CD8101000000270F",
                QUEUE_NAME + b"2",
                {},
            ),
            (
                b"payload4",
                b"4000000000003039CD8101000000270F",
                QUEUE_NAME + b"2",
                {},
            ),
        ],
    ]
    mock = sdk_mock(start=0, openQueueSync=0, enqueue_messages=messages, stop=None)
    q = queue.Queue()

    def go_on(*args):
        q.put(*args)

    session = Session(dummy_callback, on_message=go_on, _mock=mock)

    # WHEN
    session.open_queue_sync(
        QUEUE_NAME + b"1",
        read=True,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )
    session.open_queue_sync(
        QUEUE_NAME + b"2",
        read=True,
        write=False,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )

    # THEN
    m1 = q.get(timeout=1)

    assert pretty_hex(m1.guid) == "1000000000003039CD8101000000270F"
    assert m1.queue_uri == QUEUE_NAME.decode("utf8") + "1"
    assert m1.data == b"payload1"

    m2 = q.get()
    assert pretty_hex(m2.guid) == "2000000000003039CD8101000000270F"
    assert m2.queue_uri == QUEUE_NAME.decode("utf8") + "1"
    assert m2.data == b"payload2"

    m3 = q.get()
    assert pretty_hex(m3.guid) == "3000000000003039CD8101000000270F"
    assert m3.queue_uri == QUEUE_NAME.decode("utf8") + "2"
    assert m3.data == b"payload3"

    m4 = q.get()
    assert pretty_hex(m4.guid) == "4000000000003039CD8101000000270F"
    assert m4.queue_uri == QUEUE_NAME.decode("utf8") + "2"
    assert m4.data == b"payload4"


@pytest.mark.parametrize(
    "params",
    [
        (b"p",),
        (b"p", b"0000000000003039CD8101000000270F"),
        (b"p", b"0000000000003039CD8101000000270F", QUEUE_NAME),
    ],
)
def test_mock_enforces_all_message_params(params):
    messages = [[params]]
    mock = sdk_mock(start=0, openQueueSync=0, enqueue_messages=messages, stop=None)
    q = queue.Queue()

    def go_on(*args):
        q.put(*args)

    session = Session(dummy_callback, on_message=go_on, _mock=mock)

    # WHEN
    with pytest.raises(Exception) as exc:
        session.open_queue_sync(
            QUEUE_NAME,
            read=True,
            write=True,
            consumer_priority=0,
            max_unconfirmed_messages=0,
            max_unconfirmed_bytes=0,
        )

    # THEN
    assert exc.type is IndexError


def test_enqueue_messages_with_invalid_guid():
    messages = [
        [
            (
                b"fea",
                b"100000000003039CD8101000000270F",
                QUEUE_NAME,
                {},
                {},
            )
        ]
    ]
    mock = sdk_mock(start=0, openQueueSync=0, enqueue_messages=messages, stop=None)
    q = queue.Queue()

    def go_on(*args):
        q.put(*args)

    session = Session(dummy_callback, on_message=go_on, _mock=mock)

    # WHEN
    with pytest.raises(Exception) as exc:
        session.open_queue_sync(
            QUEUE_NAME,
            read=True,
            write=True,
            consumer_priority=0,
            max_unconfirmed_messages=0,
            max_unconfirmed_bytes=0,
        )

    # THEN
    assert exc.type is RuntimeError
    assert exc.match("^Invalid GUID provided$")


def test_enqueue_messages_with_invalid_queue():
    messages = [
        [(b"fea", b"1000000000003039CD8101000000270F", QUEUE_NAME + b"1", {}, {})]
    ]
    mock = sdk_mock(start=0, openQueueSync=0, enqueue_messages=messages, stop=None)
    q = queue.Queue()

    def go_on(*args):
        q.put(*args)

    session = Session(dummy_callback, on_message=go_on, _mock=mock)

    # WHEN
    with pytest.raises(Exception) as exc:
        session.open_queue_sync(
            QUEUE_NAME,
            read=True,
            write=True,
            consumer_priority=0,
            max_unconfirmed_messages=0,
            max_unconfirmed_bytes=0,
        )

    # THEN
    assert exc.type is RuntimeError
    assert exc.match("^Failed to get queue$")


def test_multiple_ack_consumption():
    # GIVEN
    q1 = queue.Queue()
    q2 = queue.Queue()

    q1_name = QUEUE_NAME + b"1"
    q2_name = QUEUE_NAME + b"2"

    def callback_1(*args):
        q1.put(*args)

    def callback_2(*args):
        q2.put(*args)

    acks = [
        [
            (0, b"1000000000003039CD8101000000270F", q1_name, callback_1),
            (-2, b"FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF", q2_name, callback_2),
        ],
        [
            (-100, b"FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF", q1_name, callback_1),
            (-101, b"FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF", q2_name, callback_2),
        ],
    ]

    mock = sdk_mock(start=0, openQueueSync=0, post=0, enqueue_acks=acks, stop=None)

    session = Session(dummy_callback, _mock=mock)

    # WHEN
    session.open_queue_sync(
        q1_name,
        read=False,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )
    session.open_queue_sync(
        q2_name,
        read=True,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )
    session.post(q1_name, b"fea")
    session.post(q2_name, b"fea")

    # THEN
    ack = q1.get(timeout=1)
    assert ack.status == AckStatus.SUCCESS
    assert pretty_hex(ack.guid) == "1000000000003039CD8101000000270F"
    assert ack.queue_uri == q1_name.decode("utf8")
    assert (
        repr(ack) == "<Ack[1000000000003039CD8101000000270F] SUCCESS for "
        "bmq://bmq.dummy_domain.some_namespace/dummy_queue1>"
    )

    ack = q2.get()
    assert (
        ack.status == AckStatus.UNKNOWN
    )  # the mock session converts TIMEOUT to UNKNOWN
    assert ack.guid is None
    assert ack.queue_uri == q2_name.decode("utf8")
    assert (
        repr(ack) == "<Ack UNKNOWN for "
        "bmq://bmq.dummy_domain.some_namespace/dummy_queue2>"
    )

    ack = q1.get()
    assert ack.status == AckStatus.LIMIT_MESSAGES
    assert ack.guid is None
    assert ack.queue_uri == q1_name.decode("utf8")
    assert (
        repr(ack) == "<Ack LIMIT_MESSAGES for "
        "bmq://bmq.dummy_domain.some_namespace/dummy_queue1>"
    )

    ack = q2.get()
    assert ack.status == AckStatus.LIMIT_BYTES
    assert ack.guid is None
    assert ack.queue_uri == q2_name.decode("utf8")
    assert (
        repr(ack) == "<Ack LIMIT_BYTES for "
        "bmq://bmq.dummy_domain.some_namespace/dummy_queue2>"
    )


def test_enqueue_acks_with_invalid_guid():
    acks = [[(0, b"100000000003039CD8101000000270F", QUEUE_NAME, dummy_callback)]]
    mock = sdk_mock(start=0, openQueueSync=0, enqueue_acks=acks, post=0, stop=None)

    session = Session(dummy_callback, _mock=mock)
    session.open_queue_sync(
        QUEUE_NAME,
        read=False,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )

    # WHEN
    with pytest.raises(Exception) as exc:
        session.post(QUEUE_NAME, b"fea")

    # THEN
    assert exc.type is RuntimeError
    assert exc.match("^Invalid GUID provided$")


def test_enqueue_acks_with_invalid_queue():
    acks = [
        [(0, b"1000000000003039CD8101000000270F", QUEUE_NAME + b"1", dummy_callback)]
    ]
    mock = sdk_mock(start=0, openQueueSync=0, enqueue_acks=acks, post=0, stop=None)

    session = Session(dummy_callback, _mock=mock)
    session.open_queue_sync(
        QUEUE_NAME,
        read=False,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )

    # WHEN
    with pytest.raises(Exception) as exc:
        session.post(QUEUE_NAME, b"fea")

    # THEN
    assert exc.type is RuntimeError
    assert exc.match("^Failed to get queue$")


def test_receiving_message_properties_success():
    # GIVEN
    messages = [
        [
            (
                b"payload1",
                b"1000000000003039CD8101000000270F",
                QUEUE_NAME + b"1",
                {
                    b"a_bool": (True, BOOL),
                    b"test1": (b"a", CHAR),
                    b"test5": (b"af\xC3\xA4ae", STRING),
                    b"test6": (b"ab\0\xC3\0", BINARY),
                    b"an_int16": (12345, SHORT),
                    b"an_int32": (31254, INT32),
                    b"an_int64": (54321, INT64),
                },
            ),
        ],
    ]
    mock = sdk_mock(start=0, openQueueSync=0, enqueue_messages=messages, stop=None)
    q = queue.Queue()

    def go_on(*args):
        q.put(*args)

    session = Session(dummy_callback, on_message=go_on, _mock=mock)

    # WHEN
    session.open_queue_sync(
        QUEUE_NAME + b"1",
        read=True,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )

    # THEN
    m1 = q.get(timeout=1)

    assert pretty_hex(m1.guid) == "1000000000003039CD8101000000270F"
    assert m1.queue_uri == QUEUE_NAME.decode("utf8") + "1"
    assert m1.data == b"payload1"
    assert m1.properties == {
        "a_bool": True,
        "test1": b"a",
        "test5": "af\xE4ae",
        "test6": b"ab\0\xC3\0",
        "an_int16": 12345,
        "an_int32": 31254,
        "an_int64": 54321,
    }
    assert m1.property_types == {
        "a_bool": PropertyType.BOOL,
        "test1": PropertyType.CHAR,
        "test5": PropertyType.STRING,
        "test6": PropertyType.BINARY,
        "an_int16": PropertyType.SHORT,
        "an_int32": PropertyType.INT32,
        "an_int64": PropertyType.INT64,
    }


@pytest.mark.parametrize(
    "properties, p_type, expected_value",
    [
        ({b"test": (b"", BINARY)}, PropertyType.BINARY, b""),
        ({b"test": (b"", STRING)}, PropertyType.STRING, ""),
    ],
)
def test_receiving_empty_does_not_raise(properties, p_type, expected_value):
    # GIVEN
    messages = [
        [
            (
                b"payload1",
                b"1000000000003039CD8101000000270F",
                QUEUE_NAME + b"1",
                properties,
            ),
        ],
    ]
    mock = sdk_mock(start=0, openQueueSync=0, enqueue_messages=messages, stop=None)
    q = queue.Queue()

    def go_on(*args):
        q.put(*args)

    session = Session(dummy_callback, on_message=go_on, _mock=mock)

    # WHEN
    session.open_queue_sync(
        QUEUE_NAME + b"1",
        read=True,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )

    # THEN
    m1 = q.get(timeout=1)

    assert m1.properties == {"test": expected_value}
    assert m1.property_types == {"test": p_type}


def test_interface_error_on_non_utf8_string_property():
    # GIVEN
    messages = [
        [
            (
                b"payload1",
                b"1000000000003039CD8101000000270F",
                QUEUE_NAME + b"1",
                {b"prop": (b"\xC3", STRING)},
            ),
        ],
    ]
    mock = sdk_mock(start=0, openQueueSync=0, enqueue_messages=messages, stop=None)
    q = queue.Queue()

    def record_events(*args):
        q.put(*args)

    session = Session(record_events, on_message=dummy_callback, _mock=mock)

    # WHEN
    session.open_queue_sync(
        QUEUE_NAME + b"1",
        read=True,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )

    # THEN
    expected_error = "STRING property 'prop' has non-UTF-8 data\n"
    assert repr(q.get()) == "<InterfaceError: %s>" % expected_error
