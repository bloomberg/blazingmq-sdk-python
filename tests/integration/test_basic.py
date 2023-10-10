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

import gc
import queue
import subprocess
import sys
import textwrap
import weakref

from blazingmq import Session
from blazingmq import session_events
import mock
import pytest


def test_on_session_events_processed():
    # GIVEN
    spy = mock.MagicMock()

    def callback(*args):
        spy(*args)

    session = Session(callback)

    # WHEN
    session.stop()

    # THEN
    assert spy.call_args_list == [
        mock.call(session_events.Connected(None)),
        mock.call(session_events.Disconnected(None)),
    ]


def test_raising_in_session_callback(capsys):
    # GIVEN
    class CustomException(Exception):
        pass

    def callback(*args):
        raise CustomException

    session = Session(callback)

    # WHEN
    session.stop()

    # THEN
    out, err = capsys.readouterr()
    assert "Traceback (most recent call last)" in err
    assert "CustomException" in err
    assert err.count("raise CustomException") == 2


def test_session_stopped_atexit():
    # GIVEN
    program = textwrap.dedent(
        """
        import blazingmq
        # make sure this works even if monkey-patched
        blazingmq._ext.ensure_stop_session = print
        import threading
        import os
        import atexit
        #
        atexit.register(print, "first atexit handler")
        e = threading.Event()
        def event_handler(event):
            print(event)
            if isinstance(event, blazingmq.session_events.Connected):
                e.set()
        s = blazingmq.Session(event_handler, print)
        e.wait()
        atexit.register(print, "last atexit handler")
        """
    )

    # WHEN
    process = subprocess.Popen(
        [sys.executable, "-Wignore", "-c", program],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()

    # THEN
    msg = b"<Connected>\nlast atexit handler\n<Disconnected>\nfirst atexit handler\n"
    assert msg == stdout
    if sys.version_info[:2] >= (3, 7):
        assert stderr == b""


def test_session_ref_cycle():
    # GIVEN
    queue1 = queue.Queue()
    queue2 = queue.Queue()

    def on_session1(event):
        queue1.put(event)

    def on_session2(event):
        queue2.put(event)

    session1 = Session(on_session1)
    session2 = Session(on_session2)
    s1_ref = weakref.ref(session1)
    s2_ref = weakref.ref(session2)

    session1.other = session2
    session2.other = session1
    assert queue1.get() == session_events.Connected(None)
    assert queue2.get() == session_events.Connected(None)

    # WHEN
    del session1
    del session2
    gc.collect()

    # THEN
    assert queue1.get() == session_events.Disconnected(None)
    assert queue2.get() == session_events.Disconnected(None)
    assert s1_ref() is None
    assert s2_ref() is None


def test_session_reassignment():
    # GIVEN
    queue1 = queue.Queue()
    queue2 = queue.Queue()

    session = Session(queue1.put)
    s_ref = weakref.ref(session)
    assert queue1.get() == session_events.Connected(None)

    # WHEN
    session = Session(queue2.put)
    s_new_ref = weakref.ref(session)
    del session

    # THEN
    assert queue1.get() == session_events.Disconnected(None)
    assert queue2.get() == session_events.Connected(None)
    assert queue2.get() == session_events.Disconnected(None)
    assert s_ref() is None
    assert s_new_ref() is None


def test_session_ref_cycle_interpreter_shutdown(capsys):
    # GIVEN
    program = textwrap.dedent(
        """
        import blazingmq
        import os

        def on_session1(event):
            print("Session1:%r" % event)

        def on_session2(event):
            print("Session2:%r" % event)

        session1 = blazingmq.Session(on_session1)
        session2 = blazingmq.Session(on_session2)

        session1.other = session2
        session2.other = session1
        """
    )

    # WHEN
    process = subprocess.Popen(
        [sys.executable, "-Wignore", "-c", program],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()

    # THEN
    assert b"Session1:<Disconnected>" in stdout
    assert b"Session2:<Disconnected>" in stdout


def test_warning_multiple_on_unstopped_deallocation():
    # GIVEN
    session1 = Session(session_events.log_session_event)
    session2 = Session(session_events.log_session_event)
    session1_ref = weakref.ref(session1)
    session2_ref = weakref.ref(session2)

    # WHEN
    with pytest.warns(Warning) as record1:
        del session1

    with pytest.warns(Warning) as record2:
        del session2
    # THEN
    assert session1_ref() is None
    assert session2_ref() is None
    assert len(record1) == 1
    assert len(record2) == 1
    assert record1[0].category is UserWarning
    assert (
        "stop() not invoked before destruction of Session" in record1[0].message.args[0]
    )
    assert record2[0].category is UserWarning
    assert (
        "stop() not invoked before destruction of Session" in record2[0].message.args[0]
    )
