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
import threading
import weakref

import pytest

from blazingmq import AckStatus
from blazingmq import CompressionAlgorithmType
from blazingmq import QueueOptions
from blazingmq import Session
from blazingmq import exceptions
from blazingmq.session_events import log_session_event


def test_post_success(default_session, unique_queue, zeroed_queue_options):
    # GIVEN
    default_session.open_queue(
        unique_queue,
        read=False,
        write=True,
        options=zeroed_queue_options,
    )

    # WHEN
    default_session.post(unique_queue, b"blah")

    # THEN
    # Message was sent!


def test_post_queue_not_opened(default_session, unique_queue, zeroed_queue_options):
    # GIVEN
    default_session.open_queue(
        unique_queue,
        read=True,
        write=True,
        options=zeroed_queue_options,
    )

    # WHEN
    with pytest.raises(Exception) as exc:
        default_session.post(unique_queue + "2", b"blah")

    # THEN
    assert exc.type is exceptions.Error
    assert exc.match("^Queue not opened$")


def test_post_no_payload(default_session, unique_queue, zeroed_queue_options):
    # GIVEN
    default_session.open_queue(
        unique_queue,
        read=True,
        write=True,
        options=zeroed_queue_options,
    )

    # WHEN
    with pytest.raises(Exception) as exc:
        default_session.post(unique_queue, None)

    # THEN
    assert exc.type is TypeError


def test_post_zero_length_payload(default_session, unique_queue, zeroed_queue_options):
    # GIVEN
    default_session.open_queue(
        unique_queue,
        read=True,
        write=True,
        options=zeroed_queue_options,
    )

    # WHEN
    with pytest.raises(Exception) as exc:
        default_session.post(unique_queue, b"")

    # THEN
    assert exc.type is exceptions.Error
    assert exc.match("Failed to construct message: PAYLOAD_EMPTY")


def test_post_read_only_queue(default_session, unique_queue, zeroed_queue_options):
    # GIVEN
    default_session.open_queue(
        unique_queue,
        read=True,
        write=False,
        options=zeroed_queue_options,
    )

    # WHEN
    with pytest.raises(Exception) as exc:
        default_session.post(unique_queue, b"")

    # THEN
    assert exc.type is exceptions.Error
    assert exc.match("Failed to construct message: QUEUE_READONLY")


def test_post_consume(unique_queue):
    # GIVEN
    received = queue.Queue()

    def on_message_event(message, message_handle):
        received.put(message)

    session = Session(log_session_event, on_message=on_message_event)
    session.open_queue(
        unique_queue,
        read=True,
        write=True,
        options=QueueOptions(
            consumer_priority=1,
            max_unconfirmed_messages=1000,
            max_unconfirmed_bytes=1000,
        ),
    )

    # WHEN
    session.post(unique_queue, b"Ad astra per aspera.")
    message = received.get()

    # THEN
    session.stop()
    assert message.data == b"Ad astra per aspera."
    assert message.queue_uri == unique_queue


def test_post_with_successful_ack(default_session, unique_queue, zeroed_queue_options):
    # GIVEN
    default_session.open_queue(
        unique_queue,
        read=False,
        write=True,
        options=zeroed_queue_options,
    )
    q = queue.Queue()

    def go_on(*args):
        q.put(*args)

    # WHEN
    default_session.post(unique_queue, b"hello", on_ack=go_on)
    ack = q.get()

    # THEN
    assert ack.status == AckStatus.SUCCESS
    assert isinstance(ack.guid, bytes)
    assert len(ack.guid) == 16
    assert ack.queue_uri == unique_queue


def test_post_with_non_callable(
    default_session, unique_queue, capsys, zeroed_queue_options
):
    # GIVEN
    default_session.open_queue(
        unique_queue,
        read=False,
        write=True,
        options=zeroed_queue_options,
    )
    go_on = object()

    # WHEN
    default_session.post(unique_queue, b"hello", on_ack=go_on)
    default_session.close_queue(unique_queue)

    # THEN
    out, err = capsys.readouterr()
    assert "Traceback" in err
    assert "TypeError" in err
    assert "not callable" in err


def test_post_callable_lifetime_maintained_and_not_leaky(
    default_session, unique_queue, zeroed_queue_options
):
    # GIVEN
    default_session.open_queue(
        unique_queue,
        read=False,
        write=True,
        options=zeroed_queue_options,
    )
    e = threading.Event()
    cb_q = queue.Queue()

    def go_on(*args):
        e.wait()
        cb_q.put(*args)

    cb_ref = weakref.ref(go_on)
    default_session.post(unique_queue, b"hello", on_ack=go_on)
    default_session.post(unique_queue, b"hello", on_ack=go_on)

    # WHEN
    del go_on
    cb_alive_after_del = cb_ref() is not None
    e.set()
    default_session.close_queue(unique_queue)  # ensure all acks delivered

    # THEN
    assert cb_q.qsize() == 2
    assert cb_alive_after_del
    assert not cb_ref()


def test_session_with_valid_compression(unique_queue, zeroed_queue_options):
    # GIVEN
    session = Session(
        log_session_event,
        message_compression_algorithm=CompressionAlgorithmType.ZLIB,
    )
    session.open_queue(
        unique_queue, read=False, write=True, options=zeroed_queue_options
    )

    # WHEN
    acks = queue.Queue()
    session.post(unique_queue, b"payload" * 1000, on_ack=lambda ack: acks.put(ack))

    # THEN
    assert acks.get().status == AckStatus.SUCCESS
