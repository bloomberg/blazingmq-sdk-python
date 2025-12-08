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

from bsl cimport optional
from bsl cimport pair
from bsl cimport shared_ptr
from bsl.bsls cimport TimeInterval
from libcpp cimport bool as cppbool

from bmq.bmqa cimport ManualHostHealthMonitor
from bmq.bmqt cimport CompressionAlgorithmType


cdef extern from 'pybmq_ballutil.h' namespace 'BloombergLP::pybmq':
    cdef cppclass BallUtil:
        @staticmethod
        object initBallSingleton(
            object (*cb)(char*, int, char*, int, char*),
            object context,
        ) except +

        @staticmethod
        object shutDownBallSingleton() except +

cdef extern from "pybmq_session.h" namespace "BloombergLP::pybmq" nogil:
    cdef cppclass Session:
        Session(object on_session_event,
                object on_message_event,
                object on_ack_event,
                object fake_authn_credential_cb,
                const char* broker_uri,
                const char* script_name,
                CompressionAlgorithmType message_compression_algorithm,
                optional[int] num_processing_threads,
                optional[int] blob_buffer_size,
                optional[int] channel_high_watermark,
                optional[pair[int, int]] event_queue_watermarks,
                TimeInterval stats_dump_interval,
                TimeInterval connect_timeout,
                TimeInterval disconnect_timeout,
                TimeInterval open_queue_timeout,
                TimeInterval configure_queue_timeout,
                TimeInterval close_queue_timeout,
                bint monitor_host_health,
                shared_ptr[ManualHostHealthMonitor] fake_host_health_monitor_sp,
                object error,
                object broker_timeout_error,
                object mock) except+

        object start(TimeInterval) except+
        object stop(bint) except+

        object open_queue_sync(const char* queue_uri,
                               bint read,
                               bint write,
                               optional[int] consumer_priority,
                               optional[int] max_unconfirmed_messages,
                               optional[int] max_unconfirmed_bytes,
                               optional[cppbool] suspends_on_bad_host_health,
                               TimeInterval timeout) except+

        object configure_queue_sync(const char* queue_uri,
                                    optional[int] consumer_priority,
                                    optional[int] max_unconfirmed_messages,
                                    optional[int] max_unconfirmed_bytes,
                                    optional[cppbool] suspends_on_bad_host_health,
                                    TimeInterval timeout) except+

        object close_queue_sync(const char* queue_uri, TimeInterval timeout) except+

        object get_queue_options(const char* queue_uri) except+

        object post(const char* queue_uri,
                    const char* payload,
                    size_t payload_length,
                    object properties,
                    object on_ack) except+
        object confirm(const char* queue_uri, const unsigned char* guid, size_t guid_length) except+
