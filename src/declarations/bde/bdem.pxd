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

cimport bsl
cimport bsl.bslma as bslma


cdef extern from 'bdem_schema.h' nogil:

    cdef cppclass Schema 'BloombergLP::bdem_Schema':
        pass


cdef extern from 'bdem_berencoderoptions.h' nogil:

    cdef cppclass BerEncoderOptions 'BloombergLP::bdem_BerEncoderOptions':
        pass


cdef extern from 'bdem_berencoder.h' nogil:

    cdef cppclass BerEncoder 'BloombergLP::bdem_BerEncoder':

        # CREATORS
        BerEncoder(const BerEncoderOptions *options=0,
                   bslma.Allocator *allocator=0)

        int encode[TYPE](bsl.streambuf *streamBuf, const TYPE& value)

        bsl.StringRef loggedMessages() const


cdef extern from 'bdem_elemtype.h' nogil:

    cdef enum e_ElemType 'BloombergLP::bdem_ElemType::Type':
        # SCALAR
        BDEM_CHAR       'BloombergLP::bdem_ElemType::BDEM_CHAR'
        BDEM_SHORT      'BloombergLP::bdem_ElemType::BDEM_SHORT'
        BDEM_INT        'BloombergLP::bdem_ElemType::BDEM_INT'
        BDEM_INT64      'BloombergLP::bdem_ElemType::BDEM_INT64'
        BDEM_FLOAT      'BloombergLP::bdem_ElemType::BDEM_FLOAT'
        BDEM_DOUBLE     'BloombergLP::bdem_ElemType::BDEM_DOUBLE'
        BDEM_BOOL       'BloombergLP::bdem_ElemType::BDEM_BOOL'
        BDEM_STRING     'BloombergLP::bdem_ElemType::BDEM_STRING'
        BDEM_DATETIME   'BloombergLP::bdem_ElemType::BDEM_DATETIME'
        BDEM_DATETIMETZ 'BloombergLP::bdem_ElemType::BDEM_DATETIMETZ'
        BDEM_DATE       'BloombergLP::bdem_ElemType::BDEM_DATE'
        BDEM_DATETZ     'BloombergLP::bdem_ElemType::BDEM_DATETZ'
        BDEM_TIME       'BloombergLP::bdem_ElemType::BDEM_TIME'
        BDEM_TIMETZ     'BloombergLP::bdem_ElemType::BDEM_TIMETZ'

        # ARRAY
        BDEM_BOOL_ARRAY 'BloombergLP::bdem_ElemType::BDEM_BOOL_ARRAY'
        BDEM_CHAR_ARRAY 'BloombergLP::bdem_ElemType::BDEM_CHAR_ARRAY'
