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
import subprocess
import sys
import textwrap
import time

import pytest

from blazingmq import AckStatus
from blazingmq import QueueOptions
from blazingmq import Session
from blazingmq.session_events import log_session_event


def script_wrapper(queue, script):
    return textwrap.dedent(
        """
            import signal

            import examples.{} as script

            script.QUEUE_URI="{}"

            if hasattr(script, "on_signal"):
                signal.signal(signal.SIGINT, script.on_signal)  # handle CTRL-C
                signal.signal(signal.SIGTERM, script.on_signal)

            script.main()
        """
    ).format(script, queue)


def run_wrapper(queue, script):
    # Allow the examples to be imported
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.dirname(__file__) + "./../.."
    if "PYTHONPATH" in os.environ:
        env["PYTHONPATH"] += ":" + os.environ["PYTHONPATH"]
    process = subprocess.Popen(
        [sys.executable, "-Wignore", "-u", "-c", script_wrapper(queue, script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    return process


def test_example_producer(unique_queue):
    # GIVEN
    process = run_wrapper(unique_queue, "producer")
    stdout, stderr = process.communicate()

    # WHEN
    if sys.version_info[:2] >= (3, 7):
        assert stderr == b""

    q = queue.Queue()

    session = Session(log_session_event, on_message=lambda msg, _: q.put(msg))
    session.open_queue(
        unique_queue,
        read=True,
        options=QueueOptions(max_unconfirmed_messages=100),
    )
    msg = q.get(timeout=0.5)

    # THEN
    session.stop()
    assert msg.data == b"\xde\xad\x00\x00\xbe\xef"
    assert msg.queue_uri == unique_queue
    assert msg.properties == {}


@pytest.mark.parametrize(
    "script",
    ["consumer", "consumer2"],
)
def test_example_consumer(unique_queue, script):
    # GIVEN
    payload = b"\xde\xad\x00\x00\xbe\xef"
    session = Session(log_session_event)
    session.open_queue(
        unique_queue,
        write=True,
        options=QueueOptions(max_unconfirmed_messages=100),
    )
    print("POST")
    acks = queue.Queue()

    # WHEN
    process = run_wrapper(unique_queue, script)
    session.post(unique_queue, payload, on_ack=acks.put)
    ack = acks.get(timeout=0.5)
    session.stop()

    time.sleep(5.0)
    process.terminate()
    time.sleep(0.1)
    if process.returncode is None and process.poll() is None:
        print("terminate failed, killing process")
        process.kill()

    stdout, stderr = process.communicate()

    # THEN
    assert ack.status == AckStatus.SUCCESS
    if sys.version_info[:2] >= (3, 7):
        assert stderr == b""
    assert (
        "Confirming:  <Message[{}] for {}>".format(ack.guid.hex().upper(), unique_queue)
        in stdout.decode()
    )
