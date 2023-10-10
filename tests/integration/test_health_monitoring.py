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

from blazingmq import BasicHealthMonitor
from blazingmq import Error
from blazingmq import QueueOptions
from blazingmq import Session
from blazingmq import session_events
from blazingmq.testing import HostHealth
import mock
import pytest


def test_receiving_host_health_events():
    # GIVEN
    spy = mock.MagicMock()
    host_health = BasicHealthMonitor()
    toggled_health_twice = threading.Event()
    host_healthy_events = []

    def callback(*args):
        spy(*args)

        if isinstance(args[0], session_events.HostHealthRestored):
            host_healthy_events.append(args[0])

        if len(host_healthy_events) == 2:
            toggled_health_twice.set()

    # WHEN
    session = Session(callback, host_health_monitor=host_health)
    host_health.set_unhealthy()
    host_health.set_healthy()
    host_health.set_unhealthy()
    host_health.set_healthy()
    toggled_health_twice.wait()
    session.stop()

    # THEN
    assert spy.call_args_list == [
        mock.call(session_events.Connected(None)),
        mock.call(session_events.HostUnhealthy(None)),
        mock.call(session_events.HostHealthRestored(None)),
        mock.call(session_events.HostUnhealthy(None)),
        mock.call(session_events.HostHealthRestored(None)),
        mock.call(session_events.Disconnected(None)),
    ]


def test_enabling_real_host_health_monitoring():
    # GIVEN
    spy = mock.MagicMock()

    def callback(*args):
        spy(*args)

    # WHEN
    session = Session(callback)
    session.stop()

    # THEN
    assert spy.call_args_list == [
        mock.call(session_events.Connected(None)),
        mock.call(session_events.Disconnected(None)),
    ]


def test_disabling_host_health_monitoring():
    # GIVEN
    spy = mock.MagicMock()

    def callback(*args):
        spy(*args)

    # WHEN
    session = Session(callback, host_health_monitor=None)
    session.stop()

    # THEN
    assert spy.call_args_list == [
        mock.call(session_events.Connected(None)),
        mock.call(session_events.Disconnected(None)),
    ]


def test_queue_suspension(unique_queue):
    # GIVEN
    host_health = HostHealth()
    queue_suspended_event_received = threading.Event()

    def on_session_event(event):
        print(event)
        if isinstance(event, session_events.QueueSuspended):
            queue_suspended_event_received.set()

    session = Session(on_session_event, host_health_monitor=host_health)

    session.open_queue(
        unique_queue,
        read=False,
        write=True,
        options=QueueOptions(suspends_on_bad_host_health=True),
    )

    # WHEN
    session.post(unique_queue, b"blah")

    host_health.set_unhealthy()
    queue_suspended_event_received.wait()

    with pytest.raises(Exception) as exc:
        session.post(unique_queue, b"blah")

    session.stop()

    # THEN
    assert exc.type is Error
    assert exc.match("QUEUE_SUSPENDED")
