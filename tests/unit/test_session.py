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

import re

from blazingmq import BasicHealthMonitor
from blazingmq import CompressionAlgorithmType
from blazingmq import Error
from blazingmq import QueueOptions
from blazingmq import Session
from blazingmq._messages import create_message
from blazingmq._session import DEFAULT_TIMEOUT
from blazingmq.testing import HostHealth
import pytest

from .support import dummy_callback
from .support import make_session
from .support import mock


@mock.patch("blazingmq._session.ExtSession")
def test_session_constructed(ext_cls):
    # GIVEN
    ext_cls.mock_add_spec([])

    def dummy1():
        pass

    def dummy2():
        pass

    # WHEN
    Session(
        dummy1,
        on_message=dummy2,
        broker="some_uri",
        timeout=60.0,
        host_health_monitor=None,
    )

    # THEN
    ext_cls.assert_called_once_with(
        dummy1,
        on_message=dummy2,
        broker=b"some_uri",
        timeout=60.0,
        message_compression_algorithm=CompressionAlgorithmType.NONE,
        monitor_host_health=False,
        fake_host_health_monitor=None,
    )


@mock.patch("blazingmq._session.ExtSession")
def test_session_basic_monitor(ext_cls):
    # GIVEN
    ext_cls.mock_add_spec([])

    def dummy1():
        pass

    def dummy2():
        pass

    monitor = BasicHealthMonitor()

    # WHEN
    Session(
        dummy1,
        on_message=dummy2,
        broker="some_uri",
        timeout=60.0,
        host_health_monitor=monitor,
    )

    # THEN
    ext_cls.assert_called_once_with(
        dummy1,
        on_message=dummy2,
        broker=b"some_uri",
        timeout=60.0,
        message_compression_algorithm=CompressionAlgorithmType.NONE,
        monitor_host_health=True,
        fake_host_health_monitor=monitor._monitor,
    )


@mock.patch("blazingmq._session.ExtSession")
def test_session_default_constructed(ext_cls):
    # GIVEN
    ext_cls.mock_add_spec([])

    def dummy1():
        pass

    def dummy2():
        pass

    # WHEN
    Session(dummy1, dummy2)

    # THEN
    ext_cls.assert_called_once_with(
        dummy1,
        on_message=dummy2,
        broker=b"tcp://localhost:30114",
        timeout=None,
        message_compression_algorithm=CompressionAlgorithmType.NONE,
        monitor_host_health=False,
        fake_host_health_monitor=None,
    )


@mock.patch("blazingmq._session.ExtSession")
def test_constructing_with_bad_type_for_host_health_monitor(ext_cls):
    # GIVEN
    ext_cls.mock_add_spec([])

    def dummy1():
        pass

    def dummy2():
        pass

    # WHEN
    with pytest.raises(Exception) as exc:
        Session(dummy1, dummy2, host_health_monitor="yes")

    # THEN
    assert exc.type is TypeError
    assert exc.match(r"host_health_monitor must be None or an instance of blazingmq\.")


def test_session_open_queue(ext):
    # GIVEN
    ext.mock_add_spec(["open_queue_sync"])
    session = make_session()
    timeout = 60.0
    queue_uri = "queue_uri"
    read = True
    write = False
    max_unconfirmed_messages = 100
    max_unconfirmed_bytes = 2048
    consumer_priority = 5
    suspends_on_bad_host_health = False

    # WHEN
    session.open_queue(
        queue_uri,
        write=write,
        read=read,
        options=QueueOptions(
            max_unconfirmed_messages=max_unconfirmed_messages,
            max_unconfirmed_bytes=max_unconfirmed_bytes,
            consumer_priority=consumer_priority,
            suspends_on_bad_host_health=suspends_on_bad_host_health,
        ),
        timeout=timeout,
    )

    # THEN
    ext.open_queue_sync.assert_called_once_with(
        b"queue_uri",
        write=write,
        read=read,
        max_unconfirmed_messages=max_unconfirmed_messages,
        max_unconfirmed_bytes=max_unconfirmed_bytes,
        consumer_priority=consumer_priority,
        timeout=timeout,
        suspends_on_bad_host_health=suspends_on_bad_host_health,
    )


def test_session_open_queue_defaults(ext):
    # GIVEN
    ext.mock_add_spec(["open_queue_sync"])
    session = make_session()

    # WHEN
    session.open_queue("queue_uri")

    # THEN
    ext.open_queue_sync.assert_called_once_with(
        b"queue_uri",
        write=False,
        read=False,
        consumer_priority=None,
        max_unconfirmed_messages=None,
        max_unconfirmed_bytes=None,
        suspends_on_bad_host_health=None,
        timeout=None,
    )


def test_session_open_queue_for_read_no_on_message_raises(ext):
    # GIVEN
    ext.mock_add_spec([])
    session = Session(dummy_callback)

    # WHEN
    with pytest.raises(Exception) as exc:
        session.open_queue("queue_uri", read=True)

    # THEN
    assert exc.type is Error
    assert exc.match(
        "Can't open queue queue_uri in read mode: no "
        "on_message callback was provided at Session construction"
    )


def test_session_open_with_suspension_without_health_monitoring(ext):
    # GIVEN
    ext.mock_add_spec(["open_queue_sync", "monitor_host_health"])
    ext.monitor_host_health = False
    session = make_session()
    queue_uri = "queue_uri"
    options = QueueOptions(suspends_on_bad_host_health=True)

    # WHEN
    with pytest.raises(Exception) as exc:
        session.open_queue(queue_uri, write=True, options=options)

    # THEN
    assert exc.type is Error
    assert exc.match(
        r"Queues cannot use suspends_on_bad_host_health if host"
        r" health monitoring was disabled when the Session was created"
    )


def test_session_close_queue(ext):
    # GIVEN
    ext.mock_add_spec(["close_queue_sync"])
    session = make_session()
    queue_uri = "queue_uri"
    timeout = 60.0

    # WHEN
    session.close_queue(queue_uri, timeout=timeout)

    # THEN
    ext.close_queue_sync.assert_called_once_with(
        b"queue_uri",
        timeout=timeout,
    )


def test_session_configure_queue(ext):
    # GIVEN
    ext.mock_add_spec(["configure_queue_sync"])
    session = make_session()
    queue_uri = "queue_uri"
    timeout = 60.0
    max_unconfirmed_messages = 100
    max_unconfirmed_bytes = 2048
    consumer_priority = 5
    suspends_on_bad_host_health = False

    # WHEN
    session.configure_queue(
        queue_uri,
        options=QueueOptions(
            max_unconfirmed_messages=max_unconfirmed_messages,
            max_unconfirmed_bytes=max_unconfirmed_bytes,
            consumer_priority=consumer_priority,
            suspends_on_bad_host_health=suspends_on_bad_host_health,
        ),
        timeout=timeout,
    )

    # THEN
    ext.configure_queue_sync.assert_called_once_with(
        b"queue_uri",
        max_unconfirmed_messages=max_unconfirmed_messages,
        max_unconfirmed_bytes=max_unconfirmed_bytes,
        consumer_priority=consumer_priority,
        suspends_on_bad_host_health=suspends_on_bad_host_health,
        timeout=timeout,
    )


def test_session_configure_queue_defaults(ext):
    # GIVEN
    ext.mock_add_spec(["configure_queue_sync"])
    session = make_session()
    queue_uri = "queue_uri"

    # WHEN
    session.configure_queue(queue_uri, options=QueueOptions())

    # THEN
    ext.configure_queue_sync.assert_called_once_with(
        b"queue_uri",
        consumer_priority=None,
        max_unconfirmed_messages=None,
        max_unconfirmed_bytes=None,
        suspends_on_bad_host_health=None,
        timeout=None,
    )


def test_session_configure_suspension_without_health_monitoring(ext):
    # GIVEN
    ext.mock_add_spec(["configure_queue_sync", "monitor_host_health"])
    ext.monitor_host_health = False
    session = make_session()
    queue_uri = "queue_uri"
    options = QueueOptions(suspends_on_bad_host_health=True)

    # WHEN
    with pytest.raises(Exception) as exc:
        session.configure_queue(queue_uri, options=options)

    # THEN
    assert exc.type is Error
    assert exc.match(
        r"Queues cannot use suspends_on_bad_host_health if host"
        r" health monitoring was disabled when the Session was created"
    )


def test_session_stop(ext):
    # GIVEN
    ext.mock_add_spec(["stop"])
    session = make_session()

    # WHEN
    session.stop()

    # THEN
    ext.stop.assert_called_once_with()


def test_session_post_no_ack_no_properties(ext):
    # GIVEN
    ext.mock_add_spec(["post"])
    session = make_session()

    # WHEN
    session.post(
        "queue_uri",
        b"data",
    )

    # THEN
    ext.post.assert_called_once_with(
        b"queue_uri",
        b"data",
        properties=None,
        on_ack=None,
    )


def test_session_post_with_ack(ext):
    # GIVEN
    ext.mock_add_spec(["post"])
    session = make_session()

    def dummy():
        pass

    # WHEN
    session.post("queue_uri", b"data", on_ack=dummy)

    # THEN
    ext.post.assert_called_once_with(
        b"queue_uri",
        b"data",
        properties=None,
        on_ack=dummy,
    )


def test_session_confirm(ext):
    # GIVEN
    ext.mock_add_spec(["confirm"])
    session = make_session()
    msg = create_message(b"data", b"guid", "queue_uri", {}, {})

    # WHEN
    session.confirm(msg)

    # THEN
    ext.confirm.assert_called_once_with(msg)


def test_session_as_context_manager(ext):
    # GIVEN
    ext.mock_add_spec(["stop"])
    session = make_session()

    # WHEN
    with session:
        pass

    # THEN
    ext.stop.assert_called_once_with()


@pytest.mark.parametrize("timeout", [None, -1.0, 2.0**63, float("inf")])
def test_session_bad_timeout(timeout):
    # GIVEN
    def dummy():
        pass

    expected_pat = re.escape(f"timeout must be greater than 0.0, was {timeout}")

    # WHEN
    with pytest.raises(Exception) as exc:
        Session(dummy, on_message=dummy, broker="some_uri", timeout=timeout)

    # THEN
    assert exc.type is ValueError
    assert exc.match(expected_pat)


@mock.patch("blazingmq._session.ExtSession")
@pytest.mark.parametrize("timeout", [None, -1.0, 0.0, 2.0**63, float("inf")])
def test_session_open_queue_bad_timeout(ext_cls, timeout):
    # GIVEN
    def dummy():
        pass

    expected_pat = re.escape(f"timeout must be greater than 0.0, was {timeout}")
    ext_cls.mock_add_spec([])
    session = Session(dummy, on_message=dummy, broker="some_uri")

    # WHEN
    with pytest.raises(Exception) as exc:
        session.open_queue("dummy uri", timeout=timeout)

    # THEN
    assert exc.type is ValueError
    assert exc.match(expected_pat)


@mock.patch("blazingmq._session.ExtSession")
@pytest.mark.parametrize("timeout", [None, -1.0, 0.0, 2.0**63, float("inf")])
def test_session_configure_queue_bad_timeout(ext_cls, timeout):
    # GIVEN

    def dummy():
        pass

    expected_pat = re.escape(f"timeout must be greater than 0.0, was {timeout}")
    dummy_uri = "dummy uri"
    ext_cls.mock_add_spec([])
    session = Session(dummy, on_message=dummy, broker="some_uri")
    session.open_queue(dummy_uri, read=True)

    # WHEN
    with pytest.raises(Exception) as exc:
        session.configure_queue("dummy uri", options=QueueOptions(), timeout=timeout)

    # THEN
    assert exc.type is ValueError
    assert exc.match(expected_pat)


@mock.patch("blazingmq._session.ExtSession")
@pytest.mark.parametrize("timeout", [None, -1.0, 0.0, 2.0**63, float("inf")])
def test_session_close_queue_bad_timeout(ext_cls, timeout):
    # GIVEN

    def dummy():
        pass

    expected_pat = re.escape(f"timeout must be greater than 0.0, was {timeout}")
    dummy_uri = "dummy uri"
    ext_cls.mock_add_spec([])
    session = Session(dummy, on_message=dummy, broker="some_uri")
    session.open_queue(dummy_uri, read=True)

    # WHEN
    with pytest.raises(Exception) as exc:
        session.close_queue("dummy uri", timeout=timeout)

    # THEN
    assert exc.type is ValueError
    assert exc.match(expected_pat)


def test_default_timeout_repr():
    # GIVEN
    # WHEN
    msg = repr(DEFAULT_TIMEOUT)
    # THEN
    assert msg == "..."


def test_basic_monitor_repr():
    # GIVEN
    # WHEN
    msg = repr(BasicHealthMonitor())
    # THEN
    assert msg == "BasicHealthMonitor()"


def test_host_health_repr():
    # GIVEN
    # WHEN
    msg = repr(HostHealth())
    # THEN
    assert msg == "BasicHealthMonitor()"
