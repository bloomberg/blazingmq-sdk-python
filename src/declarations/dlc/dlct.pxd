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

from bsl.bsls cimport Types
from libcpp cimport bool


cdef extern from "dlct_correlator.h" namespace "BloombergLP::dlct" nogil:
    cdef cppclass Correlator:
        Correlator()
        Correlator(Types.Int64)
        Types.Int64 theInteger()
        bool isInteger() const
