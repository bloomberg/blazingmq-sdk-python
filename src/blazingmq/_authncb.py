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
from typing import Callable, Optional, Tuple
from ._ext import FakeAuthnCredentialCb

CredentialTuple = Tuple[str, bytes]


class BasicAuthnCredentialCb:
    """Wrap a Python callable returning (mechanism:str, data:bytes) or None."""

    def __init__(self, callback: Callable[[], Optional[CredentialTuple]]):
        if not callable(callback):
            raise TypeError("callback must be callable")
        self._authncb = FakeAuthnCredentialCb(callback)

    def __repr__(self) -> str:
        return "BasicAuthnCredentialCb(...)"
