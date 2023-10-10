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

#ifndef INCLUDED_PYBMQ_GILACQUIREGUARD
#define INCLUDED_PYBMQ_GILACQUIREGUARD

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <bsls_keyword.h>

namespace BloombergLP {
namespace pybmq {

class GilAcquireGuard
{
  private:
    // DATA
    PyGILState_STATE d_saved_gil_state;

    // NOT IMPLEMENTED
    GilAcquireGuard(const GilAcquireGuard&) BSLS_KEYWORD_DELETED;
    GilAcquireGuard& operator=(const GilAcquireGuard&) BSLS_KEYWORD_DELETED;

  public:
    // CREATORS
    GilAcquireGuard();
    // Construct this guard, acquiring the GIL if needed.

    ~GilAcquireGuard();
    // Destroy this guard, releasing the GIL if we acquired it.
};

// ===========================================================================
//                              INLINE DEFINITIONS
// ===========================================================================

inline GilAcquireGuard::GilAcquireGuard()
: d_saved_gil_state(PyGILState_Ensure())
{
}

inline GilAcquireGuard::~GilAcquireGuard()
{
    PyGILState_Release(d_saved_gil_state);
}

}  // namespace pybmq
}  // namespace BloombergLP

#endif
