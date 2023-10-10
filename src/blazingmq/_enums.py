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

from enum import Enum


class AckStatus(Enum):
    """An enum representing the status of an Ack message

    An `AckStatus` is a status of a received `Ack` message
    which is the result of an attempted put to some particular queue.
    Anything other than `AckStatus.SUCCESS` represents a failure.
    """

    SUCCESS = object()
    UNKNOWN = object()
    TIMEOUT = object()
    NOT_CONNECTED = object()
    CANCELED = object()
    NOT_SUPPORTED = object()
    REFUSED = object()
    INVALID_ARGUMENT = object()
    NOT_READY = object()
    LIMIT_BYTES = object()
    LIMIT_MESSAGES = object()
    STORAGE_FAILURE = object()
    UNRECOGNIZED = object()
    """The `AckStatus` was not recognized by the binding layer"""

    def __repr__(self) -> str:
        # hide the unimportant value of `object()`
        return f"<{self.__class__.__name__}.{self.name}>"


class CompressionAlgorithmType(Enum):
    """An enum representing compression algorithm used by a producer"""

    NONE = object()
    ZLIB = object()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}.{self.name}>"


class PropertyType(Enum):
    """An enum representing various data types understood by BlazingMQ"""

    BOOL = object()
    CHAR = object()
    SHORT = object()
    INT32 = object()
    INT64 = object()
    STRING = object()
    BINARY = object()

    def __repr__(self) -> str:
        # hide the unimportant value of `object()`
        return f"<{self.__class__.__name__}.{self.name}>"
