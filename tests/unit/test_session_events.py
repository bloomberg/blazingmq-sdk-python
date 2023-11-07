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

import logging

import pytest

from blazingmq import _callbacks
from blazingmq import _ext
from blazingmq import session_events

from .support import mock


def test_session_event_comparison():
    # GIVEN / WHEN
    a = session_events.Connected(None)

    # THEN
    assert a == session_events.Connected(None)
    assert (a != session_events.Connected(None)) is False
    assert a != "Not a session event"
    assert a != session_events.Connected("Not a None")


def test_interface_error_repr():
    # GIVEN / WHEN
    error = "Unexpected event type: Timeout"
    e = session_events.InterfaceError(error)

    # THEN
    assert repr(e) == "<InterfaceError: Unexpected event type: Timeout>"


def test_interface_error_non_ascii_str():
    # GIVEN / WHEN
    error = "Unexpected event type: \u2014 Timeout"
    e = session_events.InterfaceError(error)

    # THEN
    r = repr(e)
    if isinstance(r, bytes):
        assert r == "<InterfaceError: Unexpected event type: \xe2\x80\x94 Timeout>"
    else:
        assert r == "<InterfaceError: Unexpected event type: \u2014 Timeout>"


def test_connected_repr():
    # GIVEN / WHEN
    e = session_events.Connected(None)

    # THEN
    assert repr(e) == "<Connected>"


def test_queue_reopened_repr():
    # GIVEN / WHEN
    e = session_events.QueueReopened("bmq://dummy_queue")

    # THEN
    assert repr(e) == "<QueueReopened: bmq://dummy_queue>"


def test_queue_reopened_eq():
    # GIVEN / WHEN
    e = session_events.QueueReopened("bmq://dummy_queue")

    # THEN
    assert e == session_events.QueueReopened("bmq://dummy_queue")
    assert e != session_events.QueueReopened("bmq://other_queue")
    assert e != session_events.Connected(None)


def test_queue_reopen_failed_repr():
    # GIVEN / WHEN
    e = session_events.QueueReopenFailed("bmq://dummy_queue", "Failed to reopen")

    # THEN
    assert repr(e) == "<QueueReopenFailed: bmq://dummy_queue Failed to reopen>"


def test_queue_reopen_failed_eq():
    # GIVEN / WHEN
    e = session_events.QueueReopenFailed("bmq://dummy_queue", "Failed to reopen")

    # THEN
    assert e == session_events.QueueReopenFailed(
        "bmq://dummy_queue", "Failed to reopen"
    )
    assert e != session_events.QueueReopenFailed("bmq://dummy_queue", "Other reason")
    assert e != session_events.QueueReopenFailed(
        "bmq://other_queue", "Failed to reopen"
    )
    assert e != session_events.Connected(None)


@pytest.mark.parametrize(
    "event_type, event_name, status_code, status_name, uri, error_description, expected_event",
    [
        (1, b"Connected", 0, b"SUCCESS", "", b"", session_events.Connected(None)),
        (
            2,
            b"Disconnected",
            0,
            b"SUCCESS",
            "",
            b"",
            session_events.Disconnected(None),
        ),
        (
            3,
            b"ConnectionLost",
            0,
            b"SUCCESS",
            "",
            b"",
            session_events.ConnectionLost(None),
        ),
        (4, b"Reconnected", 0, b"SUCCESS", b"", b"", session_events.Reconnected(None)),
        (
            5,
            b"StateRestored",
            0,
            b"SUCCESS",
            "",
            b"",
            session_events.StateRestored(None),
        ),
        (
            6,
            b"ConnectionTimeout",
            0,
            b"SUCCESS",
            "",
            b"",
            session_events.ConnectionTimeout(None),
        ),
        (
            8,
            b"QueueReopened",
            0,
            b"SUCCESS",
            "bmq://dummy_queue",
            b"",
            session_events.QueueReopened("bmq://dummy_queue"),
        ),
        (
            8,
            b"QueueReopened",
            1,
            b"NOT_SUCCESS",
            "bmq://dummy_queue",
            b"Error message",
            session_events.QueueReopenFailed(
                "bmq://dummy_queue", "Error message: NOT_SUCCESS (1)"
            ),
        ),
        (
            10,
            b"SlowConsumerNormal",
            0,
            b"SUCCESS",
            "",
            b"",
            session_events.SlowConsumerNormal(None),
        ),
        (
            11,
            b"SlowConsumerHighWaterMark",
            0,
            b"SUCCESS",
            "",
            b"",
            session_events.SlowConsumerHighWaterMark(None),
        ),
        (
            -1,
            b"Error",
            42,
            b"NOT_SUCCESS",
            "",
            b"Error message",
            session_events.Error("Error message: NOT_SUCCESS (42)"),
        ),
        (
            777,
            b"Abracadabra",
            42,
            b"NOT_SUCCESS",
            "",
            b"Error message",
            session_events.InterfaceError("Unexpected event type: Abracadabra"),
        ),
    ],
)
def test_translating_sdk_session_events(
    event_type,
    event_name,
    status_code,
    status_name,
    uri,
    error_description,
    expected_event,
):
    # GIVEN
    spy = mock.MagicMock()

    # WHEN
    _callbacks.on_session_event(
        spy,
        _ext.SESSION_EVENT_TYPE_MAPPING,
        error_description,
        (event_type, event_name, status_code, status_name, uri),
    )

    # THEN
    spy.assert_called_once()
    args, _ = spy.call_args
    assert expected_event == args[0]


def test_generating_interface_errors_without_an_sdk_event():
    # GIVEN
    spy = mock.MagicMock()

    # WHEN
    _callbacks.on_session_event(
        spy,
        _ext.SESSION_EVENT_TYPE_MAPPING,
        b"some error message",
    )

    # THEN
    spy.assert_called_once()
    args, _ = spy.call_args
    assert args == (session_events.InterfaceError("some error message"),)


@pytest.mark.parametrize(
    "event, expected_level_name",
    [
        (session_events.Connected(None), "INFO"),
        (session_events.Disconnected(None), "INFO"),
        (session_events.ConnectionLost(None), "WARN"),
        (session_events.Reconnected(None), "WARN"),
        (session_events.StateRestored(None), "INFO"),
        (session_events.ConnectionTimeout(None), "ERROR"),
        (session_events.SlowConsumerNormal(None), "INFO"),
        (session_events.SlowConsumerHighWaterMark(None), "WARN"),
        (session_events.Error("Error message: NOT_SUCCESS (42)"), "ERROR"),
        (session_events.QueueReopened("bmq://dummy_queue"), "INFO"),
        (
            session_events.QueueReopenFailed("bmq://dummy_queue", "Failed to reopen"),
            "ERROR",
        ),
        (session_events.InterfaceError("Unexpected event type: Abracadabra"), "ERROR"),
    ],
)
def test_log_session_event(event, expected_level_name, caplog):
    # GIVEN
    expected_level = getattr(logging, expected_level_name)
    expected_message = "Received session event: " + str(event)
    caplog.set_level(logging.DEBUG)

    # WHEN
    session_events.log_session_event(event)

    # THEN
    assert caplog.record_tuples == [
        ("blazingmq.session_events", expected_level, expected_message)
    ]
