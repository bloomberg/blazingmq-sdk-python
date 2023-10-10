// Copyright 2019-2023 Bloomberg Finance L.P.
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

#ifndef INCLUDED_PYBMQ_UTILS
#define INCLUDED_PYBMQ_UTILS

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <bslma_managedptr.h>
#include <bsls_assert.h>

namespace BloombergLP {
namespace pybmq {
namespace RefUtils {

namespace {  // unnamed

inline void
PyObjectDeleter(void* o, void*)
{
    Py_XDECREF(static_cast<PyObject*>(o));
}

}  // namespace

inline PyObject*
ref(PyObject* o)
{
    BSLS_ASSERT(o);
    Py_INCREF(o);
    return o;
}

inline bslma::ManagedPtr<PyObject>
toManagedPtr(PyObject* o)
{
    return bslma::ManagedPtr<PyObject>(o, 0, PyObjectDeleter);
}

}  // namespace RefUtils
}  // namespace pybmq
}  // namespace BloombergLP

#endif
