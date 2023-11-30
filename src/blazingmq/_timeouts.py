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

from typing import Optional


class Timeouts:
    """A value semantic type representing session timeouts.

    Each option can be set either by passing it as a keyword argument when
    constructing a *Timeouts* instance, or by setting it as an attribute on
    a constructed instance.

    The default for every option is `None`. When constructing a `Session`,
    either directly or using `SessionOptions`, options set to `None` are given
    reasonable default values.

    Args:
        connect_timeout:
            The maximum number of seconds to wait for connection requests on
            this session.
        disconnect_timeout:
            The maximum number of seconds to wait for disconnection requests
            on this session.
        open_queue_timeout:
            The maximum number of seconds to wait for open queue requests on
            this session.
        configure_queue_timeout:
            The maximum number of seconds to wait for configure queue requests
            on this session.
        close_queue_timeout:
            The maximum number of seconds to wait for close queue requests on
            this session.
    """

    def __init__(
        self,
        connect_timeout: Optional[float] = None,
        disconnect_timeout: Optional[float] = None,
        open_queue_timeout: Optional[float] = None,
        configure_queue_timeout: Optional[float] = None,
        close_queue_timeout: Optional[float] = None,
    ) -> None:
        self.connect_timeout = connect_timeout
        self.disconnect_timeout = disconnect_timeout
        self.open_queue_timeout = open_queue_timeout
        self.configure_queue_timeout = configure_queue_timeout
        self.close_queue_timeout = close_queue_timeout

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Timeouts):
            return False
        return (
            self.connect_timeout == other.connect_timeout
            and self.disconnect_timeout == other.disconnect_timeout
            and self.open_queue_timeout == other.open_queue_timeout
            and self.configure_queue_timeout == other.configure_queue_timeout
            and self.close_queue_timeout == other.close_queue_timeout
        )

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __repr__(self) -> str:
        attrs = (
            "connect_timeout",
            "disconnect_timeout",
            "open_queue_timeout",
            "configure_queue_timeout",
            "close_queue_timeout",
        )

        params = []
        for attr in attrs:
            value = getattr(self, attr)
            if value is not None:
                params.append(f"{attr}={value!r}")

        return f"Timeouts({', '.join(params)})"
