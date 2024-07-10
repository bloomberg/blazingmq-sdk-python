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

import atexit
from functools import partial
import logging
import weakref

from bsl cimport optional
from bsl cimport pair
from bsl cimport shared_ptr
from bsl.bsls cimport TimeInterval
from cpython.ceval cimport PyEval_InitThreads
from libcpp cimport bool as cppbool

from bmq.bmqa cimport ManualHostHealthMonitor
from bmq.bmqt cimport AckResult
from bmq.bmqt cimport CompressionAlgorithmType
from bmq.bmqt cimport HostHealthState
from bmq.bmqt cimport PropertyType
from bmq.bmqt cimport SessionEventEnum
from bmq.bmqt cimport k_DEFAULT_CONSUMER_PRIORITY
from bmq.bmqt cimport k_DEFAULT_MAX_UNCONFIRMED_BYTES
from bmq.bmqt cimport k_DEFAULT_MAX_UNCONFIRMED_MESSAGES
from bmq.bmqt cimport k_DEFAULT_SUSPENDS_ON_BAD_HOST_HEALTH
from pybmq cimport BallUtil
from pybmq cimport Session as NativeSession

from typing import Optional

from . import _callbacks
from . import _enums
from . import _messages
from . import _script_name
from . import _timeouts
from . import session_events
from .exceptions import BrokerTimeoutError
from .exceptions import Error

LOGGER = logging.getLogger(__name__)

BallUtil.initBallSingleton(_log_callback, "BlazingMQ C++ log observer")
atexit.register(BallUtil.shutDownBallSingleton)

cdef _log_callback(const char *name,
                   int level,
                   const char *filename,
                   int line,
                   const char *msg):
    if not LOGGER.isEnabledFor(level):
        return
    rec = LOGGER.makeRecord(name, level, filename, line, msg, (), None)
    LOGGER.handle(rec)


SESSION_EVENT_TYPE_MAPPING = {
    SessionEventEnum.e_CONNECTED: session_events.Connected,
    SessionEventEnum.e_DISCONNECTED: session_events.Disconnected,
    SessionEventEnum.e_CONNECTION_LOST: session_events.ConnectionLost,
    SessionEventEnum.e_RECONNECTED: session_events.Reconnected,
    SessionEventEnum.e_STATE_RESTORED: session_events.StateRestored,
    SessionEventEnum.e_CONNECTION_TIMEOUT: session_events.ConnectionTimeout,
    SessionEventEnum.e_QUEUE_REOPEN_RESULT: session_events.QueueReopened,
    SessionEventEnum.e_SLOWCONSUMER_NORMAL: session_events.SlowConsumerNormal,
    SessionEventEnum.e_SLOWCONSUMER_HIGHWATERMARK: session_events.SlowConsumerHighWaterMark,
    SessionEventEnum.e_ERROR: session_events.Error,
    SessionEventEnum.e_HOST_UNHEALTHY: session_events.HostUnhealthy,
    SessionEventEnum.e_HOST_HEALTH_RESTORED: session_events.HostHealthRestored,
    SessionEventEnum.e_QUEUE_SUSPENDED: session_events.QueueSuspended,
    SessionEventEnum.e_QUEUE_RESUMED: session_events.QueueResumed,
}


ACK_STATUS_MAPPING = {
    AckResult.e_SUCCESS: _messages.AckStatus.SUCCESS,
    AckResult.e_UNKNOWN: _messages.AckStatus.UNKNOWN,
    AckResult.e_TIMEOUT: _messages.AckStatus.TIMEOUT,
    AckResult.e_NOT_CONNECTED: _messages.AckStatus.NOT_CONNECTED,
    AckResult.e_CANCELED: _messages.AckStatus.CANCELED,
    AckResult.e_NOT_SUPPORTED: _messages.AckStatus.NOT_SUPPORTED,
    AckResult.e_REFUSED: _messages.AckStatus.REFUSED,
    AckResult.e_INVALID_ARGUMENT: _messages.AckStatus.INVALID_ARGUMENT,
    AckResult.e_NOT_READY: _messages.AckStatus.NOT_READY,
    AckResult.e_LIMIT_BYTES: _messages.AckStatus.LIMIT_BYTES,
    AckResult.e_LIMIT_MESSAGES: _messages.AckStatus.LIMIT_MESSAGES,
    AckResult.e_STORAGE_FAILURE: _messages.AckStatus.STORAGE_FAILURE,
}

PROPERTY_TYPES_TO_PY_MAPPING = {
    PropertyType.e_BOOL: _enums.PropertyType.BOOL,
    PropertyType.e_CHAR: _enums.PropertyType.CHAR,
    PropertyType.e_SHORT: _enums.PropertyType.SHORT,
    PropertyType.e_INT32: _enums.PropertyType.INT32,
    PropertyType.e_INT64: _enums.PropertyType.INT64,
    PropertyType.e_STRING: _enums.PropertyType.STRING,
    PropertyType.e_BINARY: _enums.PropertyType.BINARY,
}

PROPERTY_TYPES_FROM_PY_MAPPING = {v: k for k, v in PROPERTY_TYPES_TO_PY_MAPPING.items()}

COMPRESSION_ALGO_FROM_PY_MAPPING = {
    _enums.CompressionAlgorithmType.NONE: CompressionAlgorithmType.e_NONE,
    _enums.CompressionAlgorithmType.ZLIB: CompressionAlgorithmType.e_ZLIB,
}

DEFAULT_MAX_UNCONFIRMED_MESSAGES = k_DEFAULT_MAX_UNCONFIRMED_MESSAGES
DEFAULT_MAX_UNCONFIRMED_BYTES = k_DEFAULT_MAX_UNCONFIRMED_BYTES
DEFAULT_CONSUMER_PRIORITY = k_DEFAULT_CONSUMER_PRIORITY
DEFAULT_SUSPENDS_ON_BAD_HOST_HEALTH = k_DEFAULT_SUSPENDS_ON_BAD_HOST_HEALTH

cdef TimeInterval create_time_interval(timeout: Optional[int|float]=None):
    if timeout is not None:
        return TimeInterval(timeout)
    return TimeInterval()


cdef ensure_stop_session_impl(weakref_ext_session):
    session = weakref_ext_session()
    if session is not None:
        (<Session?>session)._session.stop(True)


def ensure_stop_session(weakref_ext_session):
    ensure_stop_session_impl(weakref_ext_session)


cdef class FakeHostHealthMonitor:
    cdef shared_ptr[ManualHostHealthMonitor] _monitor

    def __cinit__(self):
        with nogil:
            self._monitor = shared_ptr[ManualHostHealthMonitor](
                new ManualHostHealthMonitor(HostHealthState.e_HEALTHY)
            )

    def set_healthy(self):
        with nogil:
            self._monitor.get().setState(HostHealthState.e_HEALTHY)

    def set_unhealthy(self):
        with nogil:
            self._monitor.get().setState(HostHealthState.e_UNHEALTHY)


cdef class Session:
    cdef object __weakref__
    cdef NativeSession* _session
    cdef readonly object monitor_host_health

    def __cinit__(
        self,
        on_session_event not None,
        *,
        on_message=None,
        broker not None: bytes = b'tcp://localhost:30114',
        message_compression_algorithm not None=_enums.CompressionAlgorithmType.NONE,
        num_processing_threads: Optional[int] = None,
        blob_buffer_size: Optional[int] = None,
        channel_high_watermark: Optional[int] = None,
        event_queue_watermarks: Optional[tuple[int,int]] = None,
        stats_dump_interval: Optional[int|float] = None,
        timeouts: _timeouts.Timeouts = _timeouts.Timeouts(),
        monitor_host_health: bool = False,
        fake_host_health_monitor: FakeHostHealthMonitor = None,
        _mock: Optional[object] = None,
    ) -> None:
        cdef shared_ptr[ManualHostHealthMonitor] fake_host_health_monitor_sp
        cdef optional[int] c_num_processing_threads
        cdef optional[int] c_blob_buffer_size
        cdef optional[int] c_channel_high_watermark
        cdef optional[pair[int,int]] c_event_queue_watermarks
        cdef TimeInterval c_stats_dump_interval = create_time_interval(stats_dump_interval)
        cdef TimeInterval c_connect_timeout = create_time_interval(timeouts.connect_timeout)
        cdef TimeInterval c_disconnect_timeout = create_time_interval(timeouts.disconnect_timeout)
        cdef TimeInterval c_open_queue_timeout = create_time_interval(timeouts.open_queue_timeout)
        cdef TimeInterval c_configure_queue_timeout = create_time_interval(timeouts.configure_queue_timeout)
        cdef TimeInterval c_close_queue_timeout = create_time_interval(timeouts.close_queue_timeout)

        PyEval_InitThreads()

        if num_processing_threads is not None:
            c_num_processing_threads = optional[int](num_processing_threads)
        if blob_buffer_size is not None:
            c_blob_buffer_size = optional[int](blob_buffer_size)
        if channel_high_watermark is not None:
            c_channel_high_watermark = optional[int](channel_high_watermark)
        if event_queue_watermarks is not None:
            c_event_queue_watermarks = optional[pair[int,int]](
                pair[int,int](event_queue_watermarks[0], event_queue_watermarks[1]))

        self.monitor_host_health = monitor_host_health

        if fake_host_health_monitor:
            fake_host_health_monitor_sp = fake_host_health_monitor._monitor

        session_cb = partial(_callbacks.on_session_event,
                             on_session_event,
                             SESSION_EVENT_TYPE_MAPPING)
        if on_message is None:
            message_cb = partial(_callbacks.on_message_create_interface_error, on_session_event)
        else:
            message_cb = partial(
                _callbacks.on_message,
                on_message,
                weakref.ref(self),
                PROPERTY_TYPES_TO_PY_MAPPING,
            )
        ack_cb = partial(_callbacks.on_ack, ACK_STATUS_MAPPING)
        cdef char *c_broker_uri = broker
        script_name = _script_name.get_script_name()
        cdef char *c_script_name = script_name
        self._session = new NativeSession(
            session_cb,
            message_cb,
            ack_cb,
            c_broker_uri,
            c_script_name,
            COMPRESSION_ALGO_FROM_PY_MAPPING[message_compression_algorithm],
            c_num_processing_threads,
            c_blob_buffer_size,
            c_channel_high_watermark,
            c_event_queue_watermarks,
            c_stats_dump_interval,
            c_connect_timeout,
            c_disconnect_timeout,
            c_open_queue_timeout,
            c_configure_queue_timeout,
            c_close_queue_timeout,
            monitor_host_health,
            fake_host_health_monitor_sp,
            Error,
            BrokerTimeoutError,
            _mock)
        self._session.start(c_connect_timeout)
        atexit.register(ensure_stop_session_impl, weakref.ref(self))

    def stop(self) -> None:
        self._session.stop(False)

    def open_queue_sync(self,
                        queue_uri not None: bytes,
                        *,
                        read: bool,
                        write: bool,
                        consumer_priority: Optional[int] = None,
                        max_unconfirmed_messages: Optional[int] = None,
                        max_unconfirmed_bytes: Optional[int] = None,
                        suspends_on_bad_host_health: Optional[bool] = None,
                        timeout: Optional[int|float] = None) -> None:
        cdef optional[int] c_consumer_priority
        cdef optional[int] c_max_unconfirmed_messages
        cdef optional[int] c_max_unconfirmed_bytes
        cdef optional[cppbool] c_suspends_on_bad_host_health
        cdef TimeInterval c_timeout = create_time_interval(timeout)

        if consumer_priority is not None:
            c_consumer_priority = optional[int](consumer_priority)

        if max_unconfirmed_messages is not None:
            c_max_unconfirmed_messages = optional[int](max_unconfirmed_messages)

        if max_unconfirmed_bytes is not None:
            c_max_unconfirmed_bytes = optional[int](max_unconfirmed_bytes)

        if suspends_on_bad_host_health is not None:
            c_suspends_on_bad_host_health = optional[cppbool](suspends_on_bad_host_health)

        self._session.open_queue_sync(queue_uri,
                                      read,
                                      write,
                                      c_consumer_priority,
                                      c_max_unconfirmed_messages,
                                      c_max_unconfirmed_bytes,
                                      c_suspends_on_bad_host_health,
                                      c_timeout)

    def configure_queue_sync(self,
                             queue_uri not None: bytes,
                             *,
                             consumer_priority: Optional[int] = None,
                             max_unconfirmed_messages: Optional[int] = None,
                             max_unconfirmed_bytes: Optional[int] = None,
                             suspends_on_bad_host_health: Optional[bool] = None,
                             timeout: Optional[int|float] = None) -> None:
        cdef optional[int] c_consumer_priority
        cdef optional[int] c_max_unconfirmed_messages
        cdef optional[int] c_max_unconfirmed_bytes
        cdef optional[cppbool] c_suspends_on_bad_host_health
        cdef TimeInterval c_timeout = create_time_interval(timeout)

        if consumer_priority is not None:
            c_consumer_priority = optional[int](consumer_priority)

        if max_unconfirmed_messages is not None:
            c_max_unconfirmed_messages = optional[int](max_unconfirmed_messages)

        if max_unconfirmed_bytes is not None:
            c_max_unconfirmed_bytes = optional[int](max_unconfirmed_bytes)

        if suspends_on_bad_host_health is not None:
            c_suspends_on_bad_host_health = optional[cppbool](suspends_on_bad_host_health)

        self._session.configure_queue_sync(queue_uri,
                                           c_consumer_priority,
                                           c_max_unconfirmed_messages,
                                           c_max_unconfirmed_bytes,
                                           c_suspends_on_bad_host_health,
                                           c_timeout)

    def close_queue_sync(self,
                         queue_uri not None: bytes,
                         timeout: Optional[int|float] = None) -> None:
        cdef TimeInterval c_timeout = create_time_interval(timeout)
        self._session.close_queue_sync(queue_uri, c_timeout)

    def get_queue_options(self,
                          queue_uri not None: bytes) -> object:
        return self._session.get_queue_options(queue_uri)

    def post(self,
             queue_uri not None: bytes,
             payload not None: bytes,
             properties=None,
             on_ack=None) -> bytes:
        return self._session.post(
            queue_uri,
            payload,
            len(payload),
            properties,
            on_ack)

    def confirm(self, message not None) -> None:
        self._session.confirm(message.queue_uri, message.guid, len(message.guid))

    def __dealloc__(self) -> None:
        if self._session:
            try:
                self._session.stop(True)
            finally:
                del self._session
