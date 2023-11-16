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

import os
import queue
import sys
import weakref

import pytest

from blazingmq import exceptions
from blazingmq._ext import Session
from blazingmq._ext import ensure_stop_session
from blazingmq.session_events import InterfaceError

from .support import QUEUE_NAME
from .support import dummy_callback
from .support import mock
from .support import sdk_mock


def test_monitor_host_health_property():
    # GIVEN
    mock = sdk_mock(start=0, stop=None)

    # WHEN
    val1 = Session(
        dummy_callback, _mock=mock, monitor_host_health=True
    ).monitor_host_health

    val2 = Session(
        dummy_callback, _mock=mock, monitor_host_health=False
    ).monitor_host_health

    # THEN
    assert val1 is True
    assert val2 is False


def test_default_broker():
    # GIVEN
    mock = sdk_mock(start=0, stop=None)

    # WHEN
    s = Session(dummy_callback, _mock=mock)

    # THEN
    assert mock.options["broker_uri"] == "tcp://localhost:30114"
    mock.start.assert_called_once()
    mock.stop.assert_not_called()
    del s


def test_set_broker():
    # GIVEN
    mock = sdk_mock(start=0, stop=None)
    broker = b"some_uri"

    # WHEN
    s = Session(dummy_callback, broker=broker, _mock=mock)

    # THEN
    assert mock.options["broker_uri"] == broker.decode("utf8")
    mock.stop.assert_not_called()
    del s


def test_start_no_timeout():
    # GIVEN
    mock = sdk_mock(start=0, stop=None)

    # WHEN
    session = Session(dummy_callback, _mock=mock)

    # THEN
    mock.start.assert_called_once_with(timeout=0.0)
    mock.stop.assert_not_called()
    del session


def test_started_session_stopped_on_dealloc():
    # GIVEN
    mock = sdk_mock(start=0, stop=None)
    session = Session(dummy_callback, _mock=mock)

    # WHEN
    del session

    # THEN
    mock.stop.assert_called_once_with()


def test_stopped_session_not_stopped_on_dealloc():
    # GIVEN
    mock = sdk_mock(start=0, stop=None)
    session = Session(dummy_callback, _mock=mock)

    # WHEN
    session.stop()
    del session

    # THEN
    mock.start.assert_called_once_with(timeout=0.0)
    mock.stop.assert_called_once_with()


def test_start_connect_timeout():
    # GIVEN
    mock = sdk_mock(start=0, stop=None)
    timeout = 1.12345

    # WHEN
    session = Session(dummy_callback, connect_timeout=timeout, _mock=mock)

    # THEN
    mock.start.assert_called_once_with(timeout=timeout)
    mock.stop.assert_not_called()
    del session


def test_start_fails_with_timeout():
    # GIVEN
    mock = sdk_mock(start=-2, stop=None)

    # WHEN
    with pytest.raises(Exception) as exc:
        Session(dummy_callback, _mock=mock)

    # THEN
    assert exc.type is exceptions.BrokerTimeoutError
    assert exc.match("TIMEOUT")


@pytest.mark.parametrize(
    "start_rc, start_error",
    [(-1, "UNKNOWN"), (-3, "NOT_CONNECTED"), (-5, "NOT_SUPPORTED"), (-8, "NOT_READY")],
)
def test_start_fails_with_generic_error(start_rc, start_error):
    # GIVEN
    mock = sdk_mock(start=start_rc, stop=None)

    # WHEN
    with pytest.raises(Exception) as exc:
        Session(dummy_callback, _mock=mock)

    # THEN
    assert exc.type is exceptions.Error
    assert exc.match(start_error)


@pytest.mark.parametrize(
    "input,expected",
    [
        (b"/path/to/file.py", b"/path/to/file.py"),
        (b"/file/with spaces.py", b"/file/with spaces.py"),
        (b"", b"py:UNKNOWN"),
        (None, b"py:UNKNOWN"),
        (b"/touch\xe9.py", b"/touch\xe9.py"),
    ],
)
def test_process_name_override_called_correctly(monkeypatch, input, expected):
    # GIVEN
    if sys.version_info >= (3, 2) and input is not None:
        monkeypatch.setattr("__main__.__file__", os.fsdecode(input))
    else:
        monkeypatch.setattr("__main__.__file__", input)

    # WHEN
    mock = sdk_mock(start=0, stop=None)
    Session(dummy_callback, _mock=mock)

    # THEN
    assert mock.options["process_name_override"] == expected


def test_process_name_override_non_unicode(monkeypatch):
    # GIVEN
    filename = b"/path/to/some\xFFfile.py"
    if sys.version_info[0] > 2:
        monkeypatch.setattr("__main__.__file__", os.fsdecode(filename))
    else:
        monkeypatch.setattr("__main__.__file__", filename)

    # WHEN
    mock = sdk_mock(start=0, stop=None)
    Session(dummy_callback, _mock=mock)

    # THEN
    assert mock.options["process_name_override"] == filename


def test_session_timeout_passed_to_queue_defaults():
    # GIVEN
    mock = sdk_mock(start=0, stop=None)
    open_queue_timeout = 321
    configure_queue_timeout = 432
    close_queue_timeout = 543

    # WHEN
    Session(
        dummy_callback,
        open_queue_timeout=open_queue_timeout,
        configure_queue_timeout=configure_queue_timeout,
        close_queue_timeout=close_queue_timeout,
        _mock=mock,
    )

    # THEN
    assert mock.options["open_queue_timeout"] == open_queue_timeout
    assert mock.options["configure_queue_timeout"] == configure_queue_timeout
    assert mock.options["close_queue_timeout"] == close_queue_timeout


def test_session_session_options_propagated():
    # GIVEN
    mock = sdk_mock(start=0, stop=None)
    num_processing_threads = 10
    blob_buffer_size = 5000
    channel_high_watermark = 20000000
    event_queue_low_watermark = 1000000
    event_queue_high_watermark = 10000000
    stats_dump_interval = 90.0

    # WHEN
    Session(
        dummy_callback,
        num_processing_threads=num_processing_threads,
        blob_buffer_size=blob_buffer_size,
        channel_high_watermark=channel_high_watermark,
        event_queue_watermarks=(event_queue_low_watermark, event_queue_high_watermark),
        stats_dump_interval=stats_dump_interval,
        _mock=mock,
    )

    # THEN
    assert mock.options["num_processing_threads"] == num_processing_threads
    assert mock.options["blob_buffer_size"] == blob_buffer_size
    assert mock.options["channel_high_watermark"] == channel_high_watermark
    assert mock.options["event_queue_low_watermark"] == event_queue_low_watermark
    assert mock.options["event_queue_high_watermark"] == event_queue_high_watermark
    assert mock.options["stats_dump_interval"] == stats_dump_interval


def test_ensure_stop_session_callback_calls_sdk_stop():
    """Ensure that every started session is stopped by `ensure_stop_session`.

    Test that we handle the case where the session is a subclass that never
    forwards calls to our session.
    """

    # GIVEN
    class BadSession(Session):
        def __init__(self, *args, **kwargs):
            pass

        def stop(self):
            pass

    mock = sdk_mock(start=0, stop=None)
    bs = BadSession(dummy_callback, _mock=mock)

    # WHEN
    ensure_stop_session(weakref.ref(bs))

    # THEN
    mock.stop.assert_called_once_with()


def test_ensure_stop_session_callback_raises_on_non_session():
    # GIVEN
    class NonSession:
        pass

    non_session = NonSession()

    # WHEN
    with pytest.raises(Exception) as exc:
        ensure_stop_session(weakref.ref(non_session))

    # THEN
    assert exc.type is TypeError


def test_missing_on_message_event():
    # GIVEN
    messages = [[(b"data", b"1000000000003039CD8101000000270F", QUEUE_NAME, {}, {})]]
    _mock = sdk_mock(start=0, openQueueSync=0, enqueue_messages=messages, stop=None)
    spy = mock.MagicMock()
    session = Session(spy, _mock=_mock)

    # WHEN
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=False,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )

    # THEN
    spy.assert_called_once_with(
        InterfaceError("Messages received but no callback configured")
    )


def test_message_handle_keeps_session_alive():
    # GIVEN
    messages = [[(b"data", b"1000000000003039CD8101000000270F", QUEUE_NAME, {}, {})]]
    _mock = sdk_mock(start=0, openQueueSync=0, enqueue_messages=messages, stop=None)
    msg_handles = queue.Queue()

    def on_message(msg, msg_handle):
        msg_handles.put(msg_handle)

    session = Session(dummy_callback, on_message=on_message, _mock=_mock)
    session_wr = weakref.ref(session)

    # WHEN
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=False,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )
    msg_handle = msg_handles.get()
    del session

    # THEN
    assert session_wr() is not None
    del msg_handle
    assert session_wr() is None
