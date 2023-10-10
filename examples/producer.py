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

import functools
import threading

import blazingmq

QUEUE_URI = "bmq://bmq.test.mmap.priority/blazingmq-examples"


def on_ack(event: threading.Event, ack: blazingmq.Ack) -> None:
    if ack.status != blazingmq.AckStatus.SUCCESS:
        print("Received NAck: %r" % ack)
    else:
        print("Received Ack: %r" % ack)
    event.set()


def main() -> None:
    with blazingmq.Session(blazingmq.session_events.log_session_event) as session:
        print("Connected to BlazingMQ broker")
        session.open_queue(QUEUE_URI, write=True)
        event = threading.Event()
        on_ack_with_event = functools.partial(on_ack, event)
        print("Posting message")
        session.post(QUEUE_URI, b"\xde\xad\x00\x00\xbe\xef", on_ack=on_ack_with_event)
        print("Waiting for acknowledgement")
        event.wait(timeout=5.0)


if __name__ == "__main__":
    main()
