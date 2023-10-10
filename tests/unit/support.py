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

from blazingmq import PropertyType
from blazingmq import Session
from blazingmq._ext import PROPERTY_TYPES_FROM_PY_MAPPING
import mock

QUEUE_NAME = b"bmq://bmq.dummy_domain.some_namespace/dummy_queue"


def dummy_callback(*args):
    print(args)


def sdk_mock(**kwargs):
    _mock = mock.NonCallableMock(spec=list(kwargs))
    config = {k + ".return_value": v for k, v in kwargs.items()}
    _mock.configure_mock(**config)
    _mock.options = None
    mock.seal(_mock)
    return _mock


def make_session():
    return Session(dummy_callback, dummy_callback, host_health_monitor=None)


CHAR = PROPERTY_TYPES_FROM_PY_MAPPING[PropertyType.CHAR]
STRING = PROPERTY_TYPES_FROM_PY_MAPPING[PropertyType.STRING]
BINARY = PROPERTY_TYPES_FROM_PY_MAPPING[PropertyType.BINARY]
BOOL = PROPERTY_TYPES_FROM_PY_MAPPING[PropertyType.BOOL]
SHORT = PROPERTY_TYPES_FROM_PY_MAPPING[PropertyType.SHORT]
INT32 = PROPERTY_TYPES_FROM_PY_MAPPING[PropertyType.INT32]
INT64 = PROPERTY_TYPES_FROM_PY_MAPPING[PropertyType.INT64]
