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

from blazingmq import exceptions
from blazingmq._ext import Session

from .support import QUEUE_NAME
from .support import dummy_callback
from .support import sdk_mock


@pytest.mark.parametrize(
    "read, write, flags",
    [(True, True, 6), (True, False, 2), (False, True, 4)],
)
def test_open_flags_are_correct(read, write, flags):
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, stop=None)
    session = Session(dummy_callback, _mock=mock)

    # WHEN
    session.open_queue_sync(
        QUEUE_NAME,
        read=read,
        write=write,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )

    # THEN
    mock.openQueueSync.assert_called_once_with(
        uri=QUEUE_NAME,
        flags=flags,
        options={
            "consumer_priority": 0,
            "max_unconfirmed_bytes": 0,
            "max_unconfirmed_messages": 0,
            "suspends_on_bad_host_health": False,
        },
        timeout=0,
    )


def test_open_timeout_propagated():
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, stop=None)
    session = Session(dummy_callback, _mock=mock)

    # WHEN
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
        timeout=123,
    )

    # THEN
    mock.openQueueSync.assert_called_once_with(
        uri=QUEUE_NAME,
        flags=6,
        options={
            "consumer_priority": 0,
            "max_unconfirmed_bytes": 0,
            "max_unconfirmed_messages": 0,
            "suspends_on_bad_host_health": False,
        },
        timeout=123,
    )


def test_close_timeout_propagated():
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, closeQueueSync=0, stop=None)
    session = Session(dummy_callback, _mock=mock)

    # WHEN
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )
    session.close_queue_sync(
        QUEUE_NAME,
        timeout=123,
    )

    # THEN
    mock.closeQueueSync.assert_called_once_with(timeout=123)


def test_open_options_are_correctly_propagated():
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, stop=None)
    session = Session(dummy_callback, _mock=mock)

    # WHEN
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=True,
        consumer_priority=1,
        max_unconfirmed_messages=2,
        max_unconfirmed_bytes=3,
        suspends_on_bad_host_health=True,
    )

    # THEN
    mock.openQueueSync.assert_called_once_with(
        uri=QUEUE_NAME,
        flags=6,
        options={
            "consumer_priority": 1,
            "max_unconfirmed_messages": 2,
            "max_unconfirmed_bytes": 3,
            "suspends_on_bad_host_health": True,
        },
        timeout=0,
    )


def test_open_fails_with_timeout():
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=-2, stop=None)
    session = Session(dummy_callback, _mock=mock)

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
    assert exc.type is exceptions.BrokerTimeoutError
    assert exc.match("Failed to open .+dummy_queue queue: TIMEOUT: the_error_string")


@pytest.mark.parametrize(
    "open_rc, open_error",
    [(-1, "UNKNOWN"), (-3, "NOT_CONNECTED"), (-5, "NOT_SUPPORTED"), (-8, "NOT_READY")],
)
def test_open_fails_with_error(open_rc, open_error):
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=open_rc, stop=None)
    session = Session(dummy_callback, _mock=mock)

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
    assert exc.type is exceptions.Error
    assert exc.match(
        f"Failed to open .+dummy_queue queue: {open_error}: the_error_string"
    )


@pytest.mark.parametrize(
    "close_rc, close_error",
    [(-1, "UNKNOWN"), (-3, "NOT_CONNECTED"), (-5, "NOT_SUPPORTED"), (-8, "NOT_READY")],
)
def test_close_fails_with_error(close_rc, close_error):
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, closeQueueSync=close_rc, stop=None)
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
        session.close_queue_sync(QUEUE_NAME)

    # THEN
    assert exc.type is exceptions.Error
    assert exc.match(
        f"Failed to close .+dummy_queue queue: {close_error}: the_error_string"
    )


def test_close_before_open_fails():
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, stop=None)
    session = Session(dummy_callback, _mock=mock)

    # WHEN
    with pytest.raises(Exception) as exc:
        session.close_queue_sync(QUEUE_NAME)

    # THEN
    assert exc.type is exceptions.Error
    assert exc.match("^Queue not opened$")


def test_configure_before_open_fails():
    # GIVEN
    mock = sdk_mock(start=0, stop=None)
    session = Session(dummy_callback, _mock=mock)

    # WHEN
    with pytest.raises(Exception) as exc:
        session.configure_queue_sync(
            QUEUE_NAME,
            consumer_priority=0,
            max_unconfirmed_messages=0,
            max_unconfirmed_bytes=0,
        )

    # THEN
    assert exc.type is exceptions.Error
    assert exc.match("^Queue not opened$")


def test_configure_arguments_propagate():
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, configureQueueSync=0, stop=None)
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
    session.configure_queue_sync(
        QUEUE_NAME,
        consumer_priority=1,
        max_unconfirmed_messages=2,
        max_unconfirmed_bytes=3,
        suspends_on_bad_host_health=True,
    )

    # THEN
    mock.configureQueueSync.assert_called_once_with(
        options={
            "consumer_priority": 1,
            "max_unconfirmed_messages": 2,
            "max_unconfirmed_bytes": 3,
            "suspends_on_bad_host_health": True,
        },
        timeout=0.0,
    )


def test_configure_timeout_propagates():
    # Given
    mock = sdk_mock(start=0, openQueueSync=0, configureQueueSync=0, stop=None)
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
    session.configure_queue_sync(
        QUEUE_NAME,
        consumer_priority=1,
        max_unconfirmed_messages=2,
        max_unconfirmed_bytes=3,
        timeout=1.0,
        suspends_on_bad_host_health=False,
    )

    # THEN
    mock.configureQueueSync.assert_called_once_with(
        options={
            "consumer_priority": 1,
            "max_unconfirmed_messages": 2,
            "max_unconfirmed_bytes": 3,
            "suspends_on_bad_host_health": False,
        },
        timeout=1.0,
    )


def test_configure_fails_with_timeout():
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, configureQueueSync=-2, stop=None)
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
        session.configure_queue_sync(
            QUEUE_NAME,
            consumer_priority=0,
            max_unconfirmed_messages=0,
            max_unconfirmed_bytes=0,
        )

    # THEN
    assert exc.type is exceptions.BrokerTimeoutError
    assert exc.match(
        "Failed to configure .+dummy_queue queue: TIMEOUT: the_error_string"
    )
