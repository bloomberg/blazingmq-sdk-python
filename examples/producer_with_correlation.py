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
import time

import blazingmq

QUEUE_URI = "bmq://bmq.test.mmap.priority/blazingmq-examples"
MSG_COUNT = 10


def on_ack(msg_id: int, ack: blazingmq.Ack) -> None:
    if ack.status != blazingmq.AckStatus.SUCCESS:
        print(f"Received NAck for message number {msg_id}: {repr(ack)}")
    else:
        print(f"Received Ack for message number {msg_id}: {repr(ack)}")


def main() -> None:
    with blazingmq.Session(blazingmq.session_events.log_session_event) as session:
        print("Connected to BlazingMQ broker")
        session.open_queue(QUEUE_URI, write=True)
        for msg_id in range(0, MSG_COUNT):
            on_ack_with_id = functools.partial(on_ack, msg_id)
            print(f"Posting message number {msg_id}")
            session.post(QUEUE_URI, b"\xde\xad\x00\x00\xbe\xef", on_ack=on_ack_with_id)
        # Wait a short amount of time for all messages to be Ack'd or Nack'd.
        # In a production scenario, you will want a more robust solution than this.
        time.sleep(1)


if __name__ == "__main__":
    main()
