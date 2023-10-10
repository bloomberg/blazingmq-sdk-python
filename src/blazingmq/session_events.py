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

import logging
from typing import Optional

LOGGER = logging.getLogger(__name__)


class SessionEvent:
    """Base session event type"""

    def __init__(self, message: Optional[str]) -> None:
        self._message = message

    def __repr__(self) -> str:
        if self._message:
            return f"<{self.__class__.__name__}: {self._message}>"
        else:
            return f"<{self.__class__.__name__}>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SessionEvent):
            return False
        return self.__class__ is other.__class__ and self._message == other._message

    def __ne__(self, other: object) -> bool:
        return not self == other


class QueueEvent(SessionEvent):
    """Base type for session events relating to a single queue.

    Attributes:
        queue_uri (str): Queue URI this event is associated with.
    """

    def __init__(self, queue_uri: str, message: Optional[str] = None) -> None:
        self.queue_uri = queue_uri
        super().__init__(message)

    def __repr__(self) -> str:
        if self._message:
            return "<{}: {} {}>".format(
                self.__class__.__name__, self.queue_uri, self._message
            )
        else:
            return f"<{self.__class__.__name__}: {self.queue_uri}>"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented

        assert isinstance(other, QueueEvent)  # for mypy's sake
        return (
            self.__class__ is other.__class__
            and self._message == other._message
            and self.queue_uri == other.queue_uri
        )


class Connected(SessionEvent):
    """Notification of successful connection with the broker"""


class Disconnected(SessionEvent):
    """Notification of successful disconnection with the broker"""


class ConnectionLost(SessionEvent):
    """Notification of a lost connection with the broker"""


class Reconnected(SessionEvent):
    """Notification of a re-connection with the broker in case connection was lost earlier"""


class StateRestored(SessionEvent):
    """Notification of successfully restoring state of application as it was before lost
    connection or disconnection"""


class ConnectionTimeout(SessionEvent):
    """Notification that a requested connection could not be initiated in within the
    timeout period"""


class HostUnhealthy(SessionEvent):
    """Notification that the host has been marked unhealthy.

    This is emitted only if ``host_health_monitor=None`` was not provided when
    the `.Session` was created.  This will be emitted whenever the machine
    becomes unhealthy.  It is also emitted if the machine is initially unhealthy
    when the `.Session` is created.

    .. versionadded:: 0.7.0
    """


class HostHealthRestored(SessionEvent):
    """Notification that the host is no longer marked unhealthy.

    This is emitted only if ``host_health_monitor=None`` was not provided when
    the `.Session` was created.  It will be emitted once the machine is becomes
    healthy after an earlier `.HostUnhealthy` event. Before this event
    is emitted, you will receive a `QueueResumed` or `QueueResumeFailed` for
    each queue that was suspended due to ``suspends_on_bad_host_health=True``.

    .. versionadded:: 0.7.0
    """


class QueueSuspended(QueueEvent):
    """A queue that is sensitive to host health has been suspended.

    After a `.HostUnhealthy` event is emitted, any queue that was opened with
    ``suspend_on_bad_host_health=True`` will suspend operation. This event will
    be emitted once for each suspended queue.

    Note:
        If ``host_health_monitor=None`` was provided when the `.Session` was
        created, this event will never be emitted because the host will never
        be considered unhealthy.

    Attributes:
        queue_uri (str): URI of the queue that has been successfully suspended.

    .. versionadded:: 0.7.0
    """


class QueueSuspendFailed(QueueEvent):
    """A queue that is sensitive to host health could not be suspended.

    Whenever a `QueueSuspended` event would be expected, this event may be
    emitted instead if the SDK is unable to suspend the queue as expected.

    Note:
        The BlazingMQ SDK considers the failure to suspend a queue as evidence
        of an unusually serious problem with the connection to the broker, so
        if this event occurs the SDK follows it up by dropping the connection
        to the broker and trying to re-establish it.

    Attributes:
        queue_uri (str): URI of the queue that could not be suspended.

    .. versionadded:: 0.7.0
    """


class QueueResumed(QueueEvent):
    """A queue that is sensitive to host health has been resumed.

    Once an unhealthy machine becomes healthy again, the SDK will automatically
    attempt to resume each queue that was suspended when the machine became
    unhealthy. This event will be emitted once for each queue that had been
    suspended, only after which will `HostHealthRestored` be emitted.

    Attributes:
        queue_uri (str): URI of the queue that has been successfully resumed.

    .. versionadded:: 0.7.0
    """


class QueueResumeFailed(QueueEvent):
    """A queue that is sensitive to host health could not be resumed.

    Whenever a `QueueResumed` event would be expected, this event may be
    emitted instead if the SDK is unable to resume the queue as expected.

    Note:
        Unlike if suspending a queue fails, the SDK will not automatically drop
        the connection to the broker if resuming a queue fails.

    Attributes:
        queue_uri (str): URI of the queue that could not be resumed.

    .. versionadded:: 0.7.0
    """


class QueueReopened(QueueEvent):
    """A queue has been successfully reopened after a connection loss.

    If the connection with the broker is lost, `ConnectionLost` is emitted.
    Once it is reestablished, `Reconnected` is emitted, followed by either
    a `QueueReopened` or `QueueReopenFailed` for each queue that was
    previously open, and finally `StateRestored` is emitted.

    Attributes:
        queue_uri (str): URI of the queue that has been successfully reopened.
    """


class QueueReopenFailed(QueueEvent):
    """A queue couldn't be reopened after a connection loss.

    Attributes:
        queue_uri (str): URI of the queue that could not be reopened.
    """


class SlowConsumerNormal(SessionEvent):
    """Notification that the consumer has resumed acceptable rate of consumption"""


class SlowConsumerHighWaterMark(SessionEvent):
    """Notification that the consumer is consuming at the lowest rate acceptable"""


class Error(SessionEvent):
    """Notification of a miscellaneous error"""


class InterfaceError(SessionEvent):
    """The BlazingMQ SDK behaved in an unexpected way."""


def log_session_event(event: SessionEvent) -> None:
    """Log incoming session event as appropriate

    A callback that can be used as a default for the *on_session_event*
    parameter on the `.Session` object. All `.Connected`, `.Disconnected`,
    `.StateRestored`, `.SlowConsumerNormal`, and `.QueueReopened` events are
    logged at INFO level, and any `.ConnectionLost`, `.SlowConsumerHighWaterMark`,
    and `.Reconnected` events are logged at WARN level, as they may indicate issues
    with the application. Any other events are most likely an error in the
    application and are logged at ERROR level.

    Args:
        event (~blazingmq.session_events.SessionEvent): incoming `SessionEvent`
            object.
    """
    if isinstance(
        event,
        (
            Connected,
            Disconnected,
            StateRestored,
            SlowConsumerNormal,
            QueueReopened,
            HostUnhealthy,
            HostHealthRestored,
            QueueSuspended,
            QueueResumed,
        ),
    ):
        level = logging.INFO
    elif isinstance(event, (ConnectionLost, Reconnected, SlowConsumerHighWaterMark)):
        level = logging.WARN
    else:
        # ConnectionTimeout, Error, InterfaceError, QueueReopenFailed,
        # QueueSuspendFailed, QueueResumeFailed
        level = logging.ERROR

    LOGGER.log(level, "Received session event: %s", event)
