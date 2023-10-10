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

cdef extern from 'bdlt_datetime.h' namespace 'BloombergLP::bdlt' nogil:
    cdef cppclass Datetime:
        Datetime()
        Datetime(int, int, int, int, int, int, int, int)
        pass


cdef extern from 'bdlt_date.h' namespace 'BloombergLP::bdlt' nogil:

    cdef cppclass Date:
        # CREATORS
        Date()
        Date(int, int, int)

        # MANIPULATORS
        void setYearMonthDay(int year, int month, int day)


cdef extern from 'bdlt_datetz.h' namespace 'BloombergLP::bdlt' nogil:

    cdef cppclass DateTz:
        # CREATORS
        DateTz()

        # MANIPULATORS
        # void setYearMonthDay(int year, int month, int day)


cdef extern from 'bdlt_time.h' namespace 'BloombergLP::bdlt' nogil:

    cdef cppclass Time:
        # CREATORS
        Time()
        Time(int, int, int, int, int)

        # MANIPULATORS
        # Note that we elide the optional parameters to make Cython happy.
        void setTime(int hour, int minute, int second, int millisecond, int microsecond)


cdef extern from 'bdlt_timetz.h' namespace 'BloombergLP::bdlt' nogil:

    cdef cppclass TimeTz:
        # CREATORS
        TimeTz()


cdef extern from 'bdlt_datetimetz.h' namespace 'BloombergLP::bdlt' nogil:

    cdef cppclass DatetimeTz:
        # CREATORS
        DatetimeTz()

cdef extern from 'bdlt_datetimeinterval.h' namespace 'BloombergLP::bdlt' nogil:

    cdef cppclass DatetimeInterval:
        # CREATORS
        DatetimeInterval()
        DatetimeInterval(int, unsigned long long, unsigned long long, unsigned long long,
                         unsigned long long, unsigned long long)
