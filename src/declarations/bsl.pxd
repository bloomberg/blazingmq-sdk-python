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

cimport bsl.bslma as bslma


cdef extern from 'bsl_memory.h' namespace 'bsl' nogil:

    cdef cppclass shared_ptr[ELEMENT_TYPE]:
        # CREATORS
        shared_ptr()

        shared_ptr[ELEMENT_TYPE] shared_ptr[COMPATIBLE_TYPE, DELETER](
            COMPATIBLE_TYPE* ptr, DELETER *deleter)

        shared_ptr[ELEMENT_TYPE] shared_ptr[COMPATIBLE_TYPE](COMPATIBLE_TYPE* ptr)
        shared_ptr[ELEMENT_TYPE] shared_ptr[COMPATIBLE_TYPE](
            const shared_ptr[COMPATIBLE_TYPE]& other)

        # MANIPULATORS
        void createInplace(bslma.Allocator *allocator=0)

        # ACCESSORS
        ELEMENT_TYPE& operator*()

        ELEMENT_TYPE* get() const

        void reset()

cdef extern from 'bsl_memory.h' namespace 'bsl' nogil:

    cdef cppclass weak_ptr[ELEMENT_TYPE]:
        # CREATORS
        weak_ptr()

        weak_ptr[ELEMENT_TYPE] weak_ptr[COMPATIBLE_TYPE](
            const shared_ptr[COMPATIBLE_TYPE]& other)

        # ACCESSORS
        shared_ptr[ELEMENT_TYPE] lock() const

        bint expired() const

cdef extern from 'bsl_string.h' namespace 'bsl' nogil:

    cdef cppclass string:
        # CREATORS
        string(char *s)
        string()

        # MANIPULATORS
        string operator=(char *s)

        # ACCESSORS
        const char* c_str()

    cdef cppclass StringRef "BloombergLP::bslstl::StringRef":
        # CREATORS
        StringRef()

        StringRef(char *data)

        StringRef(char *data, int length)

        # StringRef(string& str)

        # ACCESSORS
        const char* data() const

        size_t length() const


cdef extern from 'bsl_streambuf.h' namespace 'bsl' nogil:

    cdef cppclass streambuf:
        pass


cdef extern from 'bsl_ostream.h' namespace 'bsl' nogil:

    cdef cppclass ostream:
        # FREE OPERATORS
        # Note that this is a declaration hack to workaround overloading
        # '::operator<<' per concrete type that would require circular
        # `cimport` statements.
        ostream& operator<<[TYPE](TYPE)

        string rdbuf() const


cdef extern from 'bsl_sstream.h' namespace 'bsl' nogil:

    cdef cppclass ostringstream(ostream):
        # ACCESSORS
        string str() const

    cdef cppclass stringstream:
        # CREATORS
        stringstream()

        # MANIPULATORS
        void str(const string buffer)

        # ACCESSORS
        streambuf* rdbuf()


cdef extern from 'bsl_vector.h' namespace 'bsl' nogil:

    cdef cppclass vector[T, ALLOCATOR=*]:
        ctypedef T value_type
        ctypedef ALLOCATOR allocator_type

        # these should really be allocator_type.size_type and
        # allocator_type.difference_type to be true to the C++ definition
        # but cython doesn't support deferred access on template arguments
        ctypedef size_t size_type
        ctypedef ptrdiff_t difference_type

        cppclass iterator:
            T& operator*()
            iterator operator++()
            iterator operator--()
            iterator operator+(size_type)
            iterator operator-(size_type)
            difference_type operator-(iterator)
            bint operator==(iterator)
            bint operator!=(iterator)
            bint operator<(iterator)
            bint operator>(iterator)
            bint operator<=(iterator)
            bint operator>=(iterator)
        cppclass reverse_iterator:
            T& operator*()
            reverse_iterator operator++()
            reverse_iterator operator--()
            reverse_iterator operator+(size_type)
            reverse_iterator operator-(size_type)
            difference_type operator-(reverse_iterator)
            bint operator==(reverse_iterator)
            bint operator!=(reverse_iterator)
            bint operator<(reverse_iterator)
            bint operator>(reverse_iterator)
            bint operator<=(reverse_iterator)
            bint operator>=(reverse_iterator)
        cppclass const_iterator(iterator):
            pass
        cppclass const_reverse_iterator(reverse_iterator):
            pass
        vector() except +
        vector(vector&) except +
        vector(size_type) except +
        vector(size_type, T&) except +
        vector(T*, T*) except +
        T& operator[](size_type)
        bint operator==(vector&, vector&)
        bint operator!=(vector&, vector&)
        bint operator<(vector&, vector&)
        bint operator>(vector&, vector&)
        bint operator<=(vector&, vector&)
        bint operator>=(vector&, vector&)
        void assign(size_type, const T&)
        void assign[input_iterator](input_iterator, input_iterator) except +
        T& at(size_type) except +
        T& back()
        iterator begin()
        const_iterator const_begin "begin"()
        size_type capacity()
        void clear()
        bint empty()
        iterator end()
        const_iterator const_end "end"()
        iterator erase(iterator)
        iterator erase(iterator, iterator)
        T& front()
        iterator insert(iterator, const T&) except +
        iterator insert(iterator, size_type, const T&) except +
        iterator insert[Iter](iterator, Iter, Iter) except +
        size_type max_size()
        void pop_back()
        void push_back(T&) except +
        reverse_iterator rbegin()
        const_reverse_iterator const_rbegin "crbegin"()
        reverse_iterator rend()
        const_reverse_iterator const_rend "crend"()
        void reserve(size_type)
        void resize(size_type) except +
        void resize(size_type, T&) except +
        size_type size()
        void swap(vector&)


cdef extern from "bsl_utility.h" namespace "bsl" nogil:
    cdef cppclass pair[T, U]:
        ctypedef T first_type
        ctypedef U second_type
        T first
        U second
        pair() except +
        pair(pair&) except +
        pair(T&, U&) except +
        bint operator==(pair&, pair&)
        bint operator!=(pair&, pair&)
        bint operator<(pair&, pair&)
        bint operator>(pair&, pair&)
        bint operator<=(pair&, pair&)
        bint operator>=(pair&, pair&)

cdef extern from 'bsl_set.h' namespace 'bsl' nogil:

    cdef cppclass set[T]:
        ctypedef T value_type
        cppclass iterator:
            T& operator*()
            iterator operator++()
            iterator operator--()
            bint operator==(iterator)
            bint operator!=(iterator)
        cppclass reverse_iterator:
            T& operator*()
            iterator operator++()
            iterator operator--()
            bint operator==(reverse_iterator)
            bint operator!=(reverse_iterator)
        cppclass const_iterator(iterator):
            pass
        cppclass const_reverse_iterator(reverse_iterator):
            pass
        set() except +
        set(set&) except +
        # set(key_compare&)
        # set& operator=(set&)
        bint operator==(set&, set&)
        bint operator!=(set&, set&)
        bint operator<(set&, set&)
        bint operator>(set&, set&)
        bint operator<=(set&, set&)
        bint operator>=(set&, set&)
        iterator begin()
        const_iterator const_begin "begin"()
        void clear()
        size_t count(const T&)
        bint empty()
        iterator end()
        const_iterator const_end "end"()
        pair[iterator, iterator] equal_range(const T&)
        # #pair[const_iterator, const_iterator] equal_range(T&)
        iterator erase(iterator)
        iterator erase(iterator, iterator)
        size_t erase(T&)
        iterator find(T&)
        const_iterator const_find "find"(T&)
        pair[iterator, bint] insert(const T&) except +
        iterator insert(iterator, const T&) except +
        void insert(iterator, iterator) except +
        # key_compare key_comp()
        iterator lower_bound(T&)
        const_iterator const_lower_bound "lower_bound"(T&)
        size_t max_size()
        reverse_iterator rbegin()
        const_reverse_iterator const_rbegin "rbegin"()
        reverse_iterator rend()
        const_reverse_iterator const_rend "rend"()
        size_t size()
        void swap(set&)
        iterator upper_bound(const T&)
        const_iterator const_upper_bound "upper_bound"(const T&)
        # value_compare value_comp()

cdef extern from "bsl_map.h" namespace "bsl" nogil:
    cdef cppclass map[T, U, COMPARE=*, ALLOCATOR=*]:
        ctypedef T key_type
        ctypedef U mapped_type
        ctypedef pair[const T, U] value_type
        ctypedef COMPARE key_compare
        ctypedef ALLOCATOR allocator_type
        cppclass iterator:
            pair[T, U]& operator*()
            iterator operator++()
            iterator operator--()
            bint operator==(iterator)
            bint operator!=(iterator)
        cppclass const_iterator:
            pair[const T, U]& operator*()
            const_iterator operator++()
            const_iterator operator--()
            bint operator==(const_iterator)
            bint operator!=(const_iterator)
        cppclass reverse_iterator:
            pair[T, U]& operator*()
            iterator operator++()
            iterator operator--()
            bint operator==(reverse_iterator)
            bint operator!=(reverse_iterator)
        cppclass const_reverse_iterator(reverse_iterator):
            pass
        map() except +
        map(map&) except +
        U& operator[](T&)
        bint operator==(map&, map&)
        bint operator!=(map&, map&)
        bint operator<(map&, map&)
        bint operator>(map&, map&)
        bint operator<=(map&, map&)
        bint operator>=(map&, map&)
        U& at(const T&) except +
        iterator begin()
        const_iterator const_begin "begin" ()
        void clear()
        size_t count(const T&)
        bint empty()
        iterator end()
        const_iterator const_end "end" ()
        pair[iterator, iterator] equal_range(const T&)
        void erase(iterator)
        void erase(iterator, iterator)
        size_t erase(const T&)
        iterator find(const T&)
        const_iterator const_find "find" (const T&)
        pair[iterator, bint] insert(pair[T, U]) except +  # XXX pair[T,U]&
        iterator insert(iterator, pair[T, U]) except +  # XXX pair[T,U]&
        iterator lower_bound(const T&)
        const_iterator const_lower_bound "lower_bound"(const T&)
        size_t max_size()
        reverse_iterator rbegin()
        const_reverse_iterator const_rbegin "rbegin"()
        reverse_iterator rend()
        const_reverse_iterator const_rend "rend"()
        size_t size()
        void swap(map&)
        iterator upper_bound(const T&)
        const_iterator const_upper_bound "upper_bound"(const T&)


cdef extern from "bsl_unordered_map.h" namespace "bsl" nogil:
    cdef cppclass unordered_map[T, U]:
        ctypedef T key_type
        ctypedef U mapped_type
        ctypedef pair[const T, U] value_type
        cppclass iterator:
            pair[T, U]& operator*()
            iterator operator++()
            iterator operator--()
            bint operator==(iterator)
            bint operator!=(iterator)
        cppclass reverse_iterator:
            pair[T, U]& operator*()
            iterator operator++()
            iterator operator--()
            bint operator==(reverse_iterator)
            bint operator!=(reverse_iterator)
        cppclass const_iterator(iterator):
            pass
        cppclass const_reverse_iterator(reverse_iterator):
            pass
        unordered_map() except +
        unordered_map(unordered_map&) except +
        U& operator[](T&)
        bint operator==(unordered_map&, unordered_map&)
        bint operator!=(unordered_map&, unordered_map&)
        bint operator<(unordered_map&, unordered_map&)
        bint operator>(unordered_map&, unordered_map&)
        bint operator<=(unordered_map&, unordered_map&)
        bint operator>=(unordered_map&, unordered_map&)
        U& at(T&)
        iterator begin()
        const_iterator const_begin "begin"()
        void clear()
        size_t count(T&)
        bint empty()
        iterator end()
        const_iterator const_end "end"()
        pair[iterator, iterator] equal_range(T&)
        iterator erase(iterator)
        iterator erase(iterator, iterator)
        size_t erase(T&)
        iterator find(T&)
        const_iterator const_find "find"(T&)
        pair[iterator, bint] insert(pair[T, U])  # XXX pair[T,U]&
        iterator insert(iterator, pair[T, U])  # XXX pair[T,U]&
        iterator lower_bound(T&)
        const_iterator const_lower_bound "lower_bound"(T&)
        size_t max_size()
        reverse_iterator rbegin()
        const_reverse_iterator const_rbegin "rbegin"()
        reverse_iterator rend()
        const_reverse_iterator const_rend "rend"()
        size_t size()
        void swap(unordered_map&)
        iterator upper_bound(T&)
        const_iterator const_upper_bound "upper_bound"(T&)
        void max_load_factor(float)
        float max_load_factor()

cdef extern from "bsl_unordered_set.h" namespace "bsl" nogil:
    cdef cppclass unordered_set[T]:
        ctypedef T value_type
        cppclass iterator:
            T& operator*()
            iterator operator++()
            iterator operator--()
            bint operator==(iterator)
            bint operator!=(iterator)
        cppclass reverse_iterator:
            T& operator*()
            iterator operator++()
            iterator operator--()
            bint operator==(reverse_iterator)
            bint operator!=(reverse_iterator)
        cppclass const_iterator(iterator):
            pass
        cppclass const_reverse_iterator(reverse_iterator):
            pass
        unordered_set() except +
        unordered_set(unordered_set&) except +
        bint operator==(unordered_set&, unordered_set&)
        bint operator!=(unordered_set&, unordered_set&)
        bint operator<(unordered_set&, unordered_set&)
        bint operator>(unordered_set&, unordered_set&)
        bint operator<=(unordered_set&, unordered_set&)
        bint operator>=(unordered_set&, unordered_set&)
        iterator begin()
        const_iterator const_begin "begin"()
        void clear()
        size_t count(T&)
        bint empty()
        iterator end()
        const_iterator const_end "end"()
        pair[iterator, iterator] equal_range(T&)
        void erase(iterator)
        void erase(iterator, iterator)
        size_t erase(T&)
        iterator find(T&)
        const_iterator const_find "find"(T&)
        pair[iterator, bint] insert(T&)
        iterator insert(iterator, T&)
        iterator lower_bound(T&)
        const_iterator const_lower_bound "lower_bound"(T&)
        size_t max_size()
        reverse_iterator rbegin()
        const_reverse_iterator const_rbegin "rbegin"()
        reverse_iterator rend()
        const_reverse_iterator const_rend "rend"()
        size_t size()
        void swap(unordered_set&)
        iterator upper_bound(T&)
        const_iterator const_upper_bound "upper_bound"(T&)

cdef extern from "bsl_optional.h" namespace "bsl" nogil:
    cdef cppclass optional[T]:
        optional()
        optional(T other)
