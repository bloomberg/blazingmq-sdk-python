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

from typing import Callable
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import Union

from blazingmq import Ack
from blazingmq import CompressionAlgorithmType
from blazingmq import Message
from blazingmq import MessageHandle
from blazingmq import PropertyType
from blazingmq import Timeouts
from blazingmq.session_events import SessionEvent

DEFAULT_MAX_UNCONFIRMED_MESSAGES: int = ...
DEFAULT_MAX_UNCONFIRMED_BYTES: int = ...
DEFAULT_CONSUMER_PRIORITY: int = ...
DEFAULT_SUSPENDS_ON_BAD_HOST_HEALTH: bool = ...

class FakeHostHealthMonitor:
    def __init__(self) -> None: ...
    def set_healthy(self) -> None: ...
    def set_unhealthy(self) -> None: ...

class Session:
    def __init__(
        self,
        on_session_event: Callable[[SessionEvent], None],
        *,
        on_message: Optional[Callable[[Message, MessageHandle], None]] = None,
        broker: bytes,
        message_compression_algorithm: CompressionAlgorithmType,
        num_processing_threads: Optional[int] = None,
        blob_buffer_size: Optional[int] = None,
        channel_high_watermark: Optional[int] = None,
        event_queue_watermarks: Optional[tuple[int, int]] = None,
        stats_dump_interval: Optional[int | float] = None,
        timeouts: Timeouts = Timeouts(),
        monitor_host_health: bool = False,
        fake_host_health_monitor: Optional[FakeHostHealthMonitor] = None,
    ) -> None: ...
    def stop(self) -> None: ...
    def open_queue_sync(
        self,
        queue_uri: bytes,
        *,
        read: bool,
        write: bool,
        consumer_priority: Optional[int] = None,
        max_unconfirmed_messages: Optional[int] = None,
        max_unconfirmed_bytes: Optional[int] = None,
        suspends_on_bad_host_health: Optional[bool] = None,
        timeout: Optional[float] = None,
    ) -> None: ...
    def close_queue_sync(
        self, queue_uri: bytes, *, timeout: Optional[float] = None
    ) -> None: ...
    def get_queue_options(self, queue_uri: bytes) -> Tuple[int, int, int]: ...
    def post(
        self,
        queue_uri: bytes,
        payload: bytes,
        *,
        properties: Optional[Dict[bytes, Tuple[Union[int, bytes], int]]] = None,
        on_ack: Optional[Callable[[Ack], None]] = None,
    ) -> bytes: ...
    def configure_queue_sync(
        self,
        queue_uri: bytes,
        *,
        max_unconfirmed_messages: Optional[int] = None,
        max_unconfirmed_bytes: Optional[int] = None,
        consumer_priority: Optional[int] = None,
        suspends_on_bad_host_health: Optional[bool] = None,
        timeout: Optional[float] = None,
    ) -> None: ...
    def confirm(self, message: Message) -> None: ...
    @property
    def monitor_host_health(self) -> bool: ...

PROPERTY_TYPES_FROM_PY_MAPPING: Dict[PropertyType, int]
