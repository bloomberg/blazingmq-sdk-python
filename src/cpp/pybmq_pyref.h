// Copyright 2019-2026 Bloomberg Finance L.P.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#ifndef INCLUDED_PYBMQ_PYREF
#define INCLUDED_PYBMQ_PYREF

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <pybmq_gilacquireguard.h>

namespace BloombergLP {
namespace pybmq {

// ===========
// class PyRef
// ===========

/// A value-semantic owning reference to a Python object.
///
/// Copying or destroying a `PyRef` adjusts the referent's reference count and
/// acquires the GIL to do so, so instances may be copied and destroyed on
/// threads that do not hold it.  This is what the BlazingMQ SDK does to
/// callbacks it has been handed, on its own IO threads.
class PyRef
{
  private:
    // DATA
    PyObject* d_object_p;

  public:
    // CREATORS
    PyRef();

    /// Create a reference to the specified `object`, which may be 0.
    explicit PyRef(PyObject* object);

    PyRef(const PyRef& other);

    ~PyRef();

    // MANIPULATORS
    PyRef& operator=(const PyRef& rhs);

    // ACCESSORS

    /// Return the referent, or 0 if this reference is empty.  The reference
    /// count is not adjusted; the caller borrows the returned pointer.
    PyObject* get() const;
};

// ===========================================================================
//                              INLINE DEFINITIONS
// ===========================================================================

inline PyRef::PyRef()
: d_object_p(0)
{
}

inline PyRef::PyRef(PyObject* object)
: d_object_p(object)
{
    GilAcquireGuard guard;
    Py_XINCREF(d_object_p);
}

inline PyRef::PyRef(const PyRef& other)
: d_object_p(other.d_object_p)
{
    GilAcquireGuard guard;
    Py_XINCREF(d_object_p);
}

inline PyRef::~PyRef()
{
    GilAcquireGuard guard;
    Py_XDECREF(d_object_p);
}

inline PyRef&
PyRef::operator=(const PyRef& rhs)
{
    if (this != &rhs) {
        GilAcquireGuard guard;
        Py_XINCREF(rhs.d_object_p);
        Py_XDECREF(d_object_p);
        d_object_p = rhs.d_object_p;
    }
    return *this;
}

inline PyObject*
PyRef::get() const
{
    return d_object_p;
}

}  // namespace pybmq
}  // namespace BloombergLP

#endif
