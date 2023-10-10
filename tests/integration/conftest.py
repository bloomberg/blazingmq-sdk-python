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

import uuid

from blazingmq import BasicHealthMonitor
from blazingmq import QueueOptions
from blazingmq import Session
from blazingmq.session_events import log_session_event
import pytest


@pytest.fixture
def unique_queue():
    return f"bmq://bmq.test.mmap.priority/{str(uuid.uuid4())}"


@pytest.fixture
def default_session():
    def handle_event(*args, **kwargs):
        print(f"Message event handler got args {args!r} kwargs {kwargs!r}")

    s = Session(log_session_event, handle_event, host_health_monitor=None)
    yield s
    s.stop()


@pytest.fixture
def health_aware_session():
    def handle_event(*args, **kwargs):
        print(f"Message event handler got args {args!r} kwargs {kwargs!r}")

    s = Session(
        log_session_event, handle_event, host_health_monitor=BasicHealthMonitor()
    )
    yield s
    s.stop()


@pytest.fixture
def zeroed_queue_options():
    return QueueOptions(
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
        consumer_priority=0,
    )
