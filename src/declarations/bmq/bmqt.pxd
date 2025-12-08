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

from libcpp cimport bool
from bsl cimport string
from bsl cimport vector


cdef extern from "bmqt_sessioneventtype.h" namespace "BloombergLP::bmqt::SessionEventType" nogil:
    cdef enum SessionEventEnum "BloombergLP::bmqt::SessionEventType::Enum":
        e_CONNECTED
        e_DISCONNECTED
        e_CONNECTION_LOST
        e_RECONNECTED
        e_STATE_RESTORED
        e_HOST_UNHEALTHY
        e_HOST_HEALTH_RESTORED
        e_QUEUE_SUSPENDED
        e_QUEUE_RESUMED
        e_CONNECTION_TIMEOUT
        e_QUEUE_REOPEN_RESULT
        e_SLOWCONSUMER_NORMAL
        e_SLOWCONSUMER_HIGHWATERMARK
        e_ERROR

cdef extern from "bmqt_resultcode.h" namespace "BloombergLP::bmqt::AckResult" nogil:
    cdef enum AckResult "BloombergLP::bmqt::AckResult::Enum":
        e_SUCCESS
        e_UNKNOWN
        e_TIMEOUT
        e_NOT_CONNECTED
        e_CANCELED
        e_NOT_SUPPORTED
        e_REFUSED
        e_INVALID_ARGUMENT
        e_NOT_READY
        e_LIMIT_MESSAGES
        e_LIMIT_BYTES
        e_STORAGE_FAILURE

cdef extern from "bmqt_propertytype.h" namespace "BloombergLP::bmqt::PropertyType" nogil:
    cdef enum PropertyType "BloombergLP::bmqt::PropertyType::Enum":
        e_BOOL
        e_CHAR
        e_SHORT
        e_INT32
        e_INT64
        e_STRING
        e_BINARY

cdef extern from "bmqt_compressionalgorithmtype.h" namespace "BloombergLP::bmqt::CompressionAlgorithmType" nogil:  # noqa: E501
    cdef enum CompressionAlgorithmType "BloombergLP::bmqt::CompressionAlgorithmType::Enum":
        e_NONE
        e_ZLIB

cdef extern from "bmqt_hosthealthstate.h" namespace "BloombergLP::bmqt::HostHealthState" nogil:  # noqa: E501
    cdef enum HostHealthState "BloombergLP::bmqt::HostHealthState::Enum":
        e_HEALTHY
        e_UNHEALTHY

cdef extern from "bmqt_queueoptions.h" namespace "BloombergLP::bmqt::QueueOptions" nogil:  # noqa: E501
    int k_DEFAULT_MAX_UNCONFIRMED_MESSAGES
    int k_DEFAULT_MAX_UNCONFIRMED_BYTES
    int k_DEFAULT_CONSUMER_PRIORITY
    bool k_DEFAULT_SUSPENDS_ON_BAD_HOST_HEALTH

cdef extern from "bmqt_authncredential.h" namespace "BloombergLP::bmqt" nogil:
    cdef cppclass AuthnCredential:
        AuthnCredential() except +
        AuthnCredential& setMechanism(const string&) except +
        AuthnCredential& setData(const vector[char]&) except +
        const string& mechanism() const
        const vector[char]& data() const
