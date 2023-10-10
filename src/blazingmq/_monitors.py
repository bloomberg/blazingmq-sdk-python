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

from ._ext import FakeHostHealthMonitor


class BasicHealthMonitor:
    """Control whether a `.Session` sees the host as healthy or unhealthy.

    When a *BasicHealthMonitor* is passed for the `.Session` constructor's
    *host_health_monitor* parameter, you can control whether the BlazingMQ
    session sees the host as healthy or unhealthy by calling the `.set_healthy`
    and `.set_unhealthy` methods.  Newly created instances default to the
    healthy state.
    """

    def __init__(self) -> None:
        self._monitor = FakeHostHealthMonitor()

    def set_healthy(self) -> None:
        """Tell any associated `.Session` that the host is healthy."""
        self._monitor.set_healthy()

    def set_unhealthy(self) -> None:
        """Tell any associated `.Session` that the host is unhealthy."""
        self._monitor.set_unhealthy()

    def __repr__(self) -> str:
        return "BasicHealthMonitor()"
