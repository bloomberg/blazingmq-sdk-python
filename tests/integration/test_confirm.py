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

import pytest

from blazingmq import Error
from blazingmq import QueueOptions
from blazingmq import Session
from blazingmq.session_events import log_session_event


def test_confirmed_message_not_redelivered(unique_queue):
    # GIVEN
    q = queue.Queue()

    def on_message(message, message_handle):
        q.put(message)

    session = Session(log_session_event, on_message=on_message)
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
    session.post(unique_queue, b"blah")
    m = q.get()
    session.confirm(m)
    session.close_queue(unique_queue)
    assert q.qsize() == 0

    # WHEN
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
    session.close_queue(unique_queue)

    # THEN
    assert q.qsize() == 0


def test_unconfirmed_message_redelivered(unique_queue):
    # GIVEN
    q = queue.Queue()

    def on_message(message, message_handle):
        q.put(message)

    session = Session(log_session_event, on_message=on_message)
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
    session.post(unique_queue, b"blah")
    m = q.get()
    session.close_queue(unique_queue)
    assert q.qsize() == 0

    # WHEN
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
    session.close_queue(unique_queue)

    # THEN
    assert q.get().guid == m.guid


def test_message_callback_racing_with_session_stop(unique_queue):
    """Ensure pybmq::Session::stop() drops its write lock before joining threads."""
    # GIVEN
    message_received = threading.Event()
    callback_exiting = threading.Event()

    def on_message(message, _):
        session.confirm(message)
        message_received.set()

        # Ensure the main thread can stop the session before we've returned.
        with pytest.raises(Error, match="Method called after session was stopped"):
            while session.get_queue_options(unique_queue):
                pass

        callback_exiting.set()

    session = Session(log_session_event, on_message=on_message)
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
    session.post(unique_queue, b"blah")
    message_received.wait()

    # WHEN
    session.stop()

    # THEN
    assert callback_exiting.is_set()
