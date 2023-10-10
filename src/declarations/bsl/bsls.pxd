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

cdef extern from "bsls_timeinterval.h" namespace "BloombergLP::bsls" nogil:

    cdef cppclass TimeInterval:
        # CREATORS
        TimeInterval()

        TimeInterval(double seconds)

        # MANIPULATORS
        TimeInterval& operator=(double rhs)


cdef extern from "bsls_types.h" namespace "BloombergLP::bsls" nogil:

    # This redefines the 'Types' struct as a class as Cython doesn't seem to
    # like the ctypedef inside a struct
    cdef cppclass Types:
        ctypedef unsigned long long Uint64
        ctypedef long long Int64
