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

from typing import Callable
from typing import Mapping
from typing import Optional
from typing import Union

from ._enums import PropertyType

PropertyValueType = Union[int, bytes, str]

PropertyValueDict = Mapping[str, PropertyValueType]

PropertyTypeDict = Mapping[str, PropertyType]

AuthnCredentialProvider = Callable[[], Optional[tuple[str, bytes]]]
"""A callable that returns authentication credentials as a tuple of
``(mechanism, data)`` tuple of ``(str, bytes)``, or ``None`` if an
error occurs while obtaining credentials.
"""
