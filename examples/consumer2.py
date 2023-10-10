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

from __future__ import annotations

import queue
import signal
from typing import Any
from typing import Optional

import blazingmq

QUEUE_URI = "bmq://bmq.test.mmap.priority/blazingmq-examples"

MESSAGES: queue.Queue[Optional[blazingmq.Message]] = queue.Queue()


def on_message(msg: blazingmq.Message, _msg_handle: blazingmq.MessageHandle) -> None:
    MESSAGES.put(msg)


def main() -> None:
    print("Starting consumer2")
    print("Send SIGTERM to exit.")
    with blazingmq.Session(
        blazingmq.session_events.log_session_event,
        on_message=on_message,
    ) as session:
        print("Connected to BlazingMQ broker")
        session.open_queue(
            QUEUE_URI,
            read=True,
            options=blazingmq.QueueOptions(
                max_unconfirmed_messages=100,
                suspends_on_bad_host_health=False,
            ),
        )

        while True:
            msg = MESSAGES.get()
            if msg is None:
                break
            print("Confirming: ", msg)
            session.confirm(msg)
        print("Waiting to receive all outstanding messages")
        session.configure_queue(QUEUE_URI, blazingmq.QueueOptions(0, 0, 0))

    print("Session stopped.")


def on_signal(signum: int, _frame: Any) -> None:
    print(f"Received signal: {signum}. Exiting...")
    MESSAGES.put(None)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, on_signal)  # handle CTRL-C
    signal.signal(signal.SIGTERM, on_signal)
    main()
