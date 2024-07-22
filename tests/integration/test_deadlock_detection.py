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

# N.B. On OSX, the
# `tests/integration/test_deadlock_detection.py::test_deadlock_detection_warning`
# test may display a dialog warning you of a crashed Python process, depending
# on your system configuration.  This crash is intentional, and is part of the
# test.

import signal
import subprocess
import sys
import textwrap


def test_deadlock_detection_warning(unique_queue):
    # GIVEN
    program = textwrap.dedent(
        """
        import blazingmq

        import resource
        import threading
        import time

        # Disable core files. This test intentionally aborts.
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

        unique_queue = {unique_queue!r}
        message_received = threading.Event()
        message_processed = threading.Event()


        def message_handler(msg, handle):
            message_received.set()
            message_processed.wait()


        def main():
            session = blazingmq.Session(
                blazingmq.session_events.log_session_event,
                message_handler,
            )
            session.open_queue(
                unique_queue,
                read=True,
                write=True,
                options=blazingmq.QueueOptions(max_unconfirmed_messages=100),
            )
            session.post(unique_queue, b"deadlock test")
            message_received.wait()


        main()
        message_processed.set()
        time.sleep(10)
        """
    ).format(unique_queue=unique_queue)

    # WHEN
    process = subprocess.Popen(
        [sys.executable, "-Wignore", "-c", program],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()

    # THEN
    assert b"Deadlock detected" in stderr
    assert process.returncode == -signal.SIGABRT
