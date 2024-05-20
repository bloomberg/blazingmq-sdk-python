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

from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import Union

from . import _six as six
from ._enums import CompressionAlgorithmType
from ._enums import PropertyType
from ._ext import DEFAULT_CONSUMER_PRIORITY
from ._ext import DEFAULT_MAX_UNCONFIRMED_BYTES
from ._ext import DEFAULT_MAX_UNCONFIRMED_MESSAGES
from ._ext import DEFAULT_SUSPENDS_ON_BAD_HOST_HEALTH
from ._ext import PROPERTY_TYPES_FROM_PY_MAPPING
from ._ext import Session as ExtSession
from ._messages import Ack
from ._messages import Message
from ._messages import MessageHandle
from ._monitors import BasicHealthMonitor
from ._timeouts import Timeouts
from ._typing import PropertyTypeDict
from ._typing import PropertyValueDict
from ._typing import PropertyValueType
from .exceptions import Error
from .session_events import SessionEvent


class DefaultTimeoutType(float):
    def __repr__(self) -> str:
        return "..."


def DefaultMonitor() -> Union[BasicHealthMonitor, None]:
    return None


DEFAULT_TIMEOUT = DefaultTimeoutType()
KNOWN_MONITORS = ("blazingmq.BasicHealthMonitor",)


def _validate_timeouts(timeouts: Timeouts) -> Timeouts:
    """Validate a `.Timeouts` instance for use by the Cython layer.

    If any of the timeouts contained within the `.Timeouts` instance are the
    `DEFAULT_TIMEOUT` sentinel or `None`, return `None`.  Otherwise, validate
    that it is within the range accepted by `bsls::TimeInterval` and return it.
    """
    return Timeouts(
        connect_timeout=_convert_timeout(timeouts.connect_timeout),
        disconnect_timeout=_convert_timeout(timeouts.disconnect_timeout),
        open_queue_timeout=_convert_timeout(timeouts.open_queue_timeout),
        configure_queue_timeout=_convert_timeout(timeouts.configure_queue_timeout),
        close_queue_timeout=_convert_timeout(timeouts.close_queue_timeout),
    )


def _convert_timeout(timeout: Optional[float]) -> Optional[float]:
    """Convert the timeout for use by the Cython layer.

    If it is the DEFAULT_TIMEOUT sentinel or None, return None.  Otherwise,
    validate that it is within the range accepted by bsls::TimeInterval and
    return it.
    """
    if timeout is DEFAULT_TIMEOUT or timeout is None:
        return None
    elif 0.0 < timeout < 2**63:
        return timeout
    raise ValueError(f"timeout must be greater than 0.0, was {timeout}")


def _convert_stats_dump_interval(interval: Optional[float]) -> Optional[float]:
    """Convert the stats dump interval for use by the Cython layer.

    If is None, return None.  Otherwise, validate that it is within the range
    accepted by bsls::TimeInterval and return it.
    """
    if interval is None:
        return interval
    if 0.0 <= interval < 2**63:
        return interval
    raise ValueError(f"stats_dump_interval must be nonnegative, was {interval}")


def _collect_properties_and_types(
    properties: Optional[PropertyValueDict],
    property_type_overrides: Optional[PropertyTypeDict],
) -> Dict[bytes, Tuple[Union[int, bytes], int]]:
    property_val_by_name: Dict[bytes, PropertyValueType] = {}
    property_type_by_name: Dict[bytes, PropertyType] = {}

    if properties:
        for name, val in properties.items():
            if isinstance(val, bool):
                default_type = PropertyType.BOOL
            elif isinstance(val, int):
                default_type = PropertyType.INT64
            elif isinstance(val, str):
                default_type = PropertyType.STRING
            elif isinstance(val, bytes):
                default_type = PropertyType.BINARY
            else:
                raise Error(
                    "Property values of type %r are not supported" % type(val).__name__
                )

            name_bytes = six.ensure_binary(name)
            property_val_by_name[name_bytes] = val
            property_type_by_name[name_bytes] = default_type

    if property_type_overrides:
        for name, override_type in property_type_overrides.items():
            name_bytes = six.ensure_binary(name)
            if name_bytes not in property_type_by_name:
                raise Error("Received override for non-existent property %r" % name)
            property_type_by_name[name_bytes] = override_type

    merged: Dict[bytes, Tuple[Union[int, bytes], int]] = {}
    for name_bytes, val in property_val_by_name.items():
        property_type = property_type_by_name[name_bytes]
        type_code = PROPERTY_TYPES_FROM_PY_MAPPING[property_type]
        if property_type is PropertyType.STRING and isinstance(val, str):
            merged[name_bytes] = (val.encode("utf-8"), type_code)
        else:
            merged[name_bytes] = (val, type_code)  # type: ignore[assignment]
            # mypy warns because `merged` can still contain Text if a Text value was
            # passed for a non-STRING field.  If so, the extension gives a nice error.

    return merged


class QueueOptions:
    """A value semantic type representing the settings for a queue.

    Each option can be set either by passing it as a keyword argument when
    constructing a *QueueOptions* instance, or by setting it as an attribute on
    a constructed instance.

    The default for every option is `None`. When calling `.configure_queue`,
    options set to `None` are not changed from their current setting. When
    calling `.open_queue`, options set to `None` are given default values.
    These default values are accessible as class attributes on the
    *QueueOptions* class.

    Args:
        max_unconfirmed_messages:
            The maximum number of messages that can be delivered to the queue
            without confirmation. If 0, no limit is imposed.  This limit can be
            reached if the queue receives messages faster than it confirms
            received messages. Once this limit is reached, at least one message
            must be confirmed before the queue will receive any more messages.
        max_unconfirmed_bytes:
            The maximum number of bytes that can be delivered to the queue
            without confirmation. If 0, no limit is imposed.  Like
            *max_unconfirmed_messages*, this limit can be reached if incoming
            messages are queued up waiting for already delivered messages to be
            confirmed.
        consumer_priority:
            The precedence of this consumer compared to other consumers of the
            same queue. The consumer with the highest priority receives the
            messages. If multiple consumers share the highest priority,
            messages are delivered to them in a round-robin fashion.
        suspends_on_bad_host_health:
            Whether or not this queue should suspend operation while the host
            machine is unhealthy. While operation is suspended, a queue opened
            with ``read=True`` will not receive messages and a queue opened
            with ``write=True`` will raise if you try to `.post` a message.
            By default, queues are not sensitive to the host's health.
    """

    DEFAULT_MAX_UNCONFIRMED_MESSAGES = DEFAULT_MAX_UNCONFIRMED_MESSAGES
    """The *max_unconfirmed_messages* used by `.open_queue` by default."""

    DEFAULT_MAX_UNCONFIRMED_BYTES = DEFAULT_MAX_UNCONFIRMED_BYTES
    """The *max_unconfirmed_bytes* used by `.open_queue` by default."""

    DEFAULT_CONSUMER_PRIORITY = DEFAULT_CONSUMER_PRIORITY
    """The *consumer_priority* used by `.open_queue` by default."""

    DEFAULT_SUSPENDS_ON_BAD_HOST_HEALTH = DEFAULT_SUSPENDS_ON_BAD_HOST_HEALTH
    """The *suspends_on_bad_host_health* used by `.open_queue` by default."""

    def __init__(
        self,
        max_unconfirmed_messages: Optional[int] = None,
        max_unconfirmed_bytes: Optional[int] = None,
        consumer_priority: Optional[int] = None,
        suspends_on_bad_host_health: Optional[bool] = None,
    ) -> None:
        self.max_unconfirmed_messages = max_unconfirmed_messages
        self.max_unconfirmed_bytes = max_unconfirmed_bytes
        self.consumer_priority = consumer_priority
        self.suspends_on_bad_host_health = suspends_on_bad_host_health

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, QueueOptions):
            return False
        return (
            self.max_unconfirmed_messages == other.max_unconfirmed_messages
            and self.max_unconfirmed_bytes == other.max_unconfirmed_bytes
            and self.consumer_priority == other.consumer_priority
            and self.suspends_on_bad_host_health == other.suspends_on_bad_host_health
        )

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __repr__(self) -> str:
        attrs = (
            "max_unconfirmed_messages",
            "max_unconfirmed_bytes",
            "consumer_priority",
            "suspends_on_bad_host_health",
        )

        params = []
        for attr in attrs:
            value = getattr(self, attr)
            if value is not None:
                params.append(f"{attr}={value!r}")

        return f"QueueOptions({', '.join(params)})"


class SessionOptions:
    """A value semantic type representing session options.

    Each option can be set either by passing it as a keyword argument when
    constructing a *SessionOptions* instance, or by setting it as an attribute
    on a constructed instance.

    The default for every option is `None`. When constructing a `Session`,
    options set to `None` are given reasonable default values.

    Args:
        message_compression_algorithm:
            The type of compression to apply to messages being posted via the
            session this object is configuring.
        timeouts:
            The maximum number of seconds to wait for requests for each
            operation on this session.  If not provided, reasonable defaults
            are used.
        host_health_monitor:
            A `.BasicHealthMonitor` is used by default, so your tests can
            control whether the session sees the machine as healthy or not by
            calling `.set_healthy` and `.set_unhealthy` on that instance.  If
            you instead pass `None`, the session will always see the machine as
            healthy, `.HostUnhealthy` and `.HostHealthRestored` events with
            never be emitted, and the *suspends_on_bad_host_health* option of
            `QueueOptions` cannot be used.
        num_processing_threads:
            The number of threads for the SDK to use for processing events.
            This defaults to 1.
        blob_buffer_size:
            The size (in bytes) of the blob buffers to use.  This defaults to
            4k.
        channel_high_watermark:
            The size (in bytes) to use for the write cache high watermark on
            the channel.  The default value is 128MB.  Note that BlazingMQ
            reserves 4MB of this value for control messages, so the actual
            watermark for data published is ``channel_high_watermark - 4MB``.
        event_queue_watermarks:
            A tuple containing the low and high notification watermark
            thresholds for the buffer containing all incoming messages from the
            broker, respectively.  A warning `.SlowConsumerHighWaterMark` is
            emitted when the buffer reaches the high watermark value, and a
            notification `.SlowConsumerNormal` is emitted when the buffer is
            back to the low watermark.
        stats_dump_interval:
            The interval (in seconds) at which to dump stats into the logs.  If
            0, disable the recurring dump of stats (final stats are always
            dumped at the end of the session).  The default is 5min; the value
            must be a multiple of 30s, in the range ``[0s - 60min]``.
    """

    def __init__(
        self,
        message_compression_algorithm: Optional[CompressionAlgorithmType] = None,
        timeouts: Optional[Timeouts] = None,
        host_health_monitor: Union[BasicHealthMonitor, None] = (DefaultMonitor()),
        num_processing_threads: Optional[int] = None,
        blob_buffer_size: Optional[int] = None,
        channel_high_watermark: Optional[int] = None,
        event_queue_watermarks: Optional[tuple[int, int]] = None,
        stats_dump_interval: Optional[float] = None,
    ) -> None:
        self.message_compression_algorithm = message_compression_algorithm
        self.timeouts = timeouts
        self.host_health_monitor = host_health_monitor
        self.num_processing_threads = num_processing_threads
        self.blob_buffer_size = blob_buffer_size
        self.channel_high_watermark = channel_high_watermark
        self.event_queue_watermarks = event_queue_watermarks
        self.stats_dump_interval = stats_dump_interval

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SessionOptions):
            return False
        return (
            self.message_compression_algorithm == other.message_compression_algorithm
            and self.timeouts == other.timeouts
            and self.host_health_monitor == other.host_health_monitor
            and self.num_processing_threads == other.num_processing_threads
            and self.blob_buffer_size == other.blob_buffer_size
            and self.channel_high_watermark == other.channel_high_watermark
            and self.event_queue_watermarks == other.event_queue_watermarks
            and self.stats_dump_interval == other.stats_dump_interval
        )

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __repr__(self) -> str:
        attrs = (
            "message_compression_algorithm",
            "timeouts",
            "host_health_monitor",
            "num_processing_threads",
            "blob_buffer_size",
            "channel_high_watermark",
            "event_queue_watermarks",
            "stats_dump_interval",
        )

        params = []
        for attr in attrs:
            value = getattr(self, attr)
            if value is not None:
                params.append(f"{attr}={value!r}")

        return f"SessionOptions({', '.join(params)})"


class Session:
    """Represents a connection with the BlazingMQ broker.

    The session represents a connection to the broker.
    This object can be manipulated to modify the state of the application from
    the point of view of the broker, including opening queues, and starting or
    stopping the connection with the broker.

    Args:
        on_session_event: a required callback to process `.SessionEvent` events
            received by the session.
        on_message: an optional callback to process `Message` objects received
            by the session.
        broker: TCP address of the broker (default: 'tcp://localhost:30114').
            If the environment variable ``BMQ_BROKER_URI`` is set, its value
            will override whatever broker address is passed via this argument.
        message_compression_algorithm: the type of compression to apply to messages
            being posted via this session object.
        timeout: maximum number of seconds to wait for requests on this
            session.  If not provided, reasonable defaults are used.  This
            argument may either be a simple ``float``, which sets the same
            timeout for each operation, or an instance of the `Timeouts` class,
            which allows setting the timeout for each operation independently.
        host_health_monitor: A `.BasicHealthMonitor` is used by default, so
            your tests can control whether the session sees the machine as
            healthy or not by calling `.set_healthy` and `.set_unhealthy` on
            that instance.  If you instead pass `None`, the session will always
            see the machine as healthy, `.HostUnhealthy` and
            `.HostHealthRestored` events will never be emitted, and the
            *suspends_on_bad_host_health* option of `QueueOptions` cannot be
            used.
        num_processing_threads: The number of threads for the SDK to use for
            processing events.  This defaults to 1.
        blob_buffer_size: The size (in bytes) of the blob buffers to use.  This
            defaults to 4k.
        channel_high_watermark: The size (in bytes) to use for the write cache
            high watermark on the channel.  The default value is 128MB.  Note
            that BlazingMQ reserves 4MB of this value for control messages, so
            the actual watermark for data published is
            ``channel_high_watermark - 4MB``.
        event_queue_watermarks: A tuple containing the low and high
            notification watermark thresholds for the buffer containing all
            incoming messages from the broker, respectively.  A warning
            `.SlowConsumerHighWaterMark` is emitted when the buffer reaches the
            high watermark value, and a notification `.SlowConsumerNormal` is
            emitted when the buffer is back to the low watermark.
        stats_dump_interval: The interval (in seconds) at which to dump stats
            into the logs.  If 0, disable the recurring dump of stats (final
            stats are always dumped at the end of the session).  The default is
            5min; the value must be a multiple of 30s, in the range
            ``[0s - 60min]``.

    Raises:
        `~blazingmq.Error`: If the session start request was not successful.
        `~blazingmq.exceptions.BrokerTimeoutError`: If the broker didn't respond
            to the request within a reasonable amount of time.
        `ValueError`: If any of the timeouts are provided and not > 0.0, or if
            the ``stats_dump_interval`` is provided and is < 0.0.
    """

    def __init__(
        self,
        on_session_event: Callable[[SessionEvent], None],
        on_message: Optional[Callable[[Message, MessageHandle], None]] = None,
        broker: str = "tcp://localhost:30114",
        message_compression_algorithm: CompressionAlgorithmType = (
            CompressionAlgorithmType.NONE
        ),
        timeout: Union[Timeouts, float] = DEFAULT_TIMEOUT,
        host_health_monitor: Union[BasicHealthMonitor, None] = (DefaultMonitor()),
        num_processing_threads: Optional[int] = None,
        blob_buffer_size: Optional[int] = None,
        channel_high_watermark: Optional[int] = None,
        event_queue_watermarks: Optional[tuple[int, int]] = None,
        stats_dump_interval: Optional[float] = None,
    ) -> None:
        if host_health_monitor is not None:
            if not isinstance(host_health_monitor, BasicHealthMonitor):
                raise TypeError(
                    f"host_health_monitor must be None or an instance of "
                    f"{' or '.join(KNOWN_MONITORS)}"
                )

        monitor_host_health = host_health_monitor is not None
        fake_host_health_monitor = getattr(host_health_monitor, "_monitor", None)

        self._has_no_on_message = on_message is None

        # Using our Timeouts class, preserve the old behavior of passing in a
        # simple float as a timeout.  Avoid setting the `connect_timeout` and
        # `disconnect_timeout`.
        if not isinstance(timeout, Timeouts):
            timeout = Timeouts(
                open_queue_timeout=timeout,
                configure_queue_timeout=timeout,
                close_queue_timeout=timeout,
            )

        self._ext = ExtSession(
            on_session_event,
            on_message=on_message,
            broker=six.ensure_binary(broker),
            message_compression_algorithm=message_compression_algorithm,
            num_processing_threads=num_processing_threads,
            blob_buffer_size=blob_buffer_size,
            channel_high_watermark=channel_high_watermark,
            event_queue_watermarks=event_queue_watermarks,
            stats_dump_interval=_convert_stats_dump_interval(stats_dump_interval),
            timeouts=_validate_timeouts(timeout),
            monitor_host_health=monitor_host_health,
            fake_host_health_monitor=fake_host_health_monitor,
        )

    @classmethod
    def with_options(
        cls,
        on_session_event: Callable[[SessionEvent], None],
        on_message: Optional[Callable[[Message, MessageHandle], None]] = None,
        broker: str = "tcp://localhost:30114",
        session_options: SessionOptions = (SessionOptions()),
    ) -> Session:
        """Construct a *Session* instance using `.SessionOptions`.

        This is the recommended way to construct a new session, as the
        `.SessionOptions` class provides an easier to use interface for
        configuring only those options you need.

        Args:
            on_session_event: a required callback to process `.SessionEvent` events
                received by the session.
            on_message: an optional callback to process `Message` objects received
                by the session.
            broker: TCP address of the broker (default: 'tcp://localhost:30114').
                If the environment variable ``BMQ_BROKER_URI`` is set, its value
                will override whatever broker address is passed via this argument.
            session_options: an instance of `.SessionOptions` that represents the
                session's configuration.

        Raises:
            `~blazingmq.Error`: If the session start request was not successful.
            `~blazingmq.exceptions.BrokerTimeoutError`: If the broker didn't respond
                to the request within a reasonable amount of time.
            `ValueError`: If any of the timeouts are provided and not > 0.0, or if
                the ``stats_dump_interval`` is provided and is < 0.0.
        """
        message_compression_algorithm = session_options.message_compression_algorithm
        if message_compression_algorithm is None:
            message_compression_algorithm = CompressionAlgorithmType.NONE

        if session_options.timeouts is None:
            return cls(
                on_session_event,
                on_message,
                broker,
                message_compression_algorithm,
                DEFAULT_TIMEOUT,
                session_options.host_health_monitor,
                session_options.num_processing_threads,
                session_options.blob_buffer_size,
                session_options.channel_high_watermark,
                session_options.event_queue_watermarks,
                session_options.stats_dump_interval,
            )
        else:
            return cls(
                on_session_event,
                on_message,
                broker,
                message_compression_algorithm,
                session_options.timeouts,
                session_options.host_health_monitor,
                session_options.num_processing_threads,
                session_options.blob_buffer_size,
                session_options.channel_high_watermark,
                session_options.event_queue_watermarks,
                session_options.stats_dump_interval,
            )

    def open_queue(
        self,
        queue_uri: str,
        read: bool = False,
        write: bool = False,
        options: QueueOptions = QueueOptions(),
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Open a queue with the specified parameters

        Open a queue at the specified *queue_uri*. The *queue_uri* is the
        identifier for any future interactions with this opened queue.

        Note:
            Invoking this method from the ``on_message`` or
            ``on_session_event`` of the `Session` or the ``on_ack`` callback of
            a posted message will cause a deadlock.

        Note:
            It's possible to override the default tier by adding an optional
            tier to the queue URI.  See `URI format`__.

        __ https://bloomberg.github.io/blazingmq/docs/apidocs/cpp_apidocs/group__bmqt__uri.html

        Args:
            queue_uri: unique resource identifier for the queue to be opened.
            read: open the queue for reading, enabling the `Session` to receive
                `Message` objects for this queue.
            write: open the queue for writing, allowing posting to this queue.
            options (~blazingmq.QueueOptions): options to configure the queue
                with
            timeout: maximum number of seconds to wait for this request.
                If not provided, the *timeout* provided to the `Session` when
                it was created it used.  If that was not provided either,
                a reasonable default is used.

        Raises:
            `~blazingmq.Error`: If the open queue request was not successful.
            `~blazingmq.exceptions.BrokerTimeoutError`: If the broker didn't
                respond to the request within a reasonable amount of time.
            `ValueError`: If *timeout* is not > 0.0.
        """
        if read and self._has_no_on_message:
            raise Error(
                "Can't open queue {} in read mode: no on_message "
                "callback was provided at Session construction".format(queue_uri)
            )

        if options.suspends_on_bad_host_health and not self._ext.monitor_host_health:
            raise Error(
                "Queues cannot use suspends_on_bad_host_health if host health"
                " monitoring was disabled when the Session was created"
            )

        self._ext.open_queue_sync(
            six.ensure_binary(queue_uri),
            read=read,
            write=write,
            consumer_priority=options.consumer_priority,
            max_unconfirmed_messages=options.max_unconfirmed_messages,
            max_unconfirmed_bytes=options.max_unconfirmed_bytes,
            suspends_on_bad_host_health=options.suspends_on_bad_host_health,
            timeout=_convert_timeout(timeout),
        )

    def close_queue(self, queue_uri: str, timeout: float = DEFAULT_TIMEOUT) -> None:
        """Close an opened queue at the specified *queue_uri*.

        Close the queue at the specified *queue_uri*. After this method
        successfully returns, the *queue_uri* will no longer correspond to valid
        queue to do any operations.

        Note:
            Invoking this method from the ``on_message`` or
            ``on_session_event`` of the `Session` or the ``on_ack`` callback of
            a posted message will cause a deadlock.

        Args:
            queue_uri: unique resource identifier for the queue to be closed.
            timeout: maximum number of seconds to wait for this request.
                If not provided, the *timeout* provided to the `Session` when
                it was created it used.  If that was not provided either,
                a reasonable default is used.

        Raises:
            `~blazingmq.Error`: If the close queue request was not successful.
            `~blazingmq.exceptions.BrokerTimeoutError`: If the broker didn't
                respond to the request within a reasonable amount of time.
            `ValueError`: If *timeout* is not > 0.0.
        """
        self._ext.close_queue_sync(
            six.ensure_binary(queue_uri),
            timeout=_convert_timeout(timeout),
        )

    def configure_queue(
        self,
        queue_uri: str,
        options: QueueOptions,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Modify the options on an opened queue at the specified *queue_uri*.

        Modify the options of the queue at the specified *queue_uri*. After this
        method successfully returns, the *queue_uri* will be configured with the
        specified *options*.

        Note:
            Invoking this method from the ``on_message`` or ``on_session_event`` of
            the `Session` or the ``on_ack`` callback of a posted message will
            cause a deadlock.

        Args:
            queue_uri: unique resource identifier for the queue to be configured.
            options (~blazingmq.QueueOptions): options to configure the queue with
            timeout: maximum number of seconds to wait for this request.
                If not provided, the *timeout* provided to the `Session` when
                it was created it used.  If that was not provided either,
                a reasonable default is used.

        Raises:
            `~blazingmq.Error`: If the configure queue request was not successful.
            `~blazingmq.exceptions.BrokerTimeoutError`: If the broker didn't
                respond to the request within a reasonable amount of time.
            `ValueError`: If *timeout* is not > 0.0.
        """
        if options.suspends_on_bad_host_health and not self._ext.monitor_host_health:
            raise Error(
                "Queues cannot use suspends_on_bad_host_health if host health"
                " monitoring was disabled when the Session was created"
            )

        self._ext.configure_queue_sync(
            six.ensure_binary(queue_uri),
            consumer_priority=options.consumer_priority,
            max_unconfirmed_messages=options.max_unconfirmed_messages,
            max_unconfirmed_bytes=options.max_unconfirmed_bytes,
            suspends_on_bad_host_health=options.suspends_on_bad_host_health,
            timeout=_convert_timeout(timeout),
        )

    def get_queue_options(self, queue_uri: str) -> QueueOptions:
        """Get configured options of an opened queue.

        Get the previously set options of an opened queue at the specified
        *queue_uri*.

        Args:
            queue_uri: unique resource identifier for the queue to be configured.

        Returns:
            `~blazingmq.QueueOptions`: The queue's configured options.

        Raises:
            `~blazingmq.Error`: If the queue with the given URI is not open, or
                its options cannot be retrieved.

        Note:
            Options that only affect message consumption, including
            *consumer_priority*, *max_unconfirmed_messages*, and
            *max_unconfirmed_bytes*, are ignored when opening or configuring
            a write-only queue, so any attempt to set those options on
            a write-only queue won't be reflected in the `QueueOptions`
            returned by a later call to *get_queue_options*.
        """
        options = self._ext.get_queue_options(six.ensure_binary(queue_uri))
        return QueueOptions(*options)

    def stop(self) -> None:
        """Teardown the broker connection

        Stop the session with the connected BlazingMQ broker which implies
        tearing down the connection. This session cannot be used to execute any
        actions after this method returns.

        Note:
            Invoking this method from the ``on_message`` or
            ``on_session_event`` of the `Session` or the ``on_ack`` callback of
            a posted message will cause a deadlock.
        """

        self._ext.stop()

    def post(
        self,
        queue_uri: str,
        message: bytes,
        properties: Optional[PropertyValueDict] = None,
        property_type_overrides: Optional[PropertyTypeDict] = None,
        on_ack: Optional[Callable[[Ack], None]] = None,
    ) -> None:
        """Post a message to an opened queue specified by *queue_uri*.

        Post the payload and optional properties and overrides to the opened
        queue specified by *queue_uri*. Optionally take an *on_ack* callback
        that is invoked with the incoming acknowledgment for the message posted.

        Args:
            queue_uri: unique resource identifier for the queue to posted to.
            message: the payload of the message.
            properties (Optional[`~blazingmq.PropertyValueDict`]): optionally
                provided properties to be associated with the message.
            property_type_overrides (Optional[`~blazingmq.PropertyTypeDict`]):
                optionally provided type overrides for the properties.
            on_ack (Optional[Callable[[~blazingmq.Ack], None]]): optionally
                specified callback which is invoked with the acknowledgment
                status of the message being posted.

        Raises:
            `~blazingmq.Error`: If the post request was not successful.
        """
        props: Optional[Dict[bytes, Tuple[Union[int, bytes], int]]] = None
        if properties or property_type_overrides:
            props = _collect_properties_and_types(properties, property_type_overrides)

        self._ext.post(
            six.ensure_binary(queue_uri),
            message,
            properties=props,
            on_ack=on_ack,
        )

    def confirm(self, message: Message) -> None:
        """Confirm the specified message from this queue.

        Mark the specified *message*, as confirmed. If successful, this will
        indicate to the BlazingMQ framework that the processing for this
        message has been completed and that the message must not be
        re-delivered, if this queue is opened again by any consumer.

        It's often more convenient to use `MessageHandle.confirm`
        instead. An instance of `MessageHandle` is received with every
        new `Message` delivered via the ``on_message`` callback.

        Args:
            message (~blazingmq.Message): message to be confirmed.

        Raises:
            `~blazingmq.Error`: If the confirm message request was not
                successful.
        """
        self._ext.confirm(message)

    def __enter__(self) -> Session:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, exc_traceback: Any) -> None:
        self.stop()
