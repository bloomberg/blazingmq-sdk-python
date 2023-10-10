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

#ifndef INCLUDED_PYBMQ_GILRELEASEGUARD
#define INCLUDED_PYBMQ_GILRELEASEGUARD

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <bsls_keyword.h>

namespace BloombergLP {
namespace pybmq {

class GilReleaseGuard
{
    // DATA
    PyThreadState* d_saved_thread_state;

    // NOT IMPLEMENTED
    GilReleaseGuard(const GilReleaseGuard&) BSLS_KEYWORD_DELETED;
    GilReleaseGuard& operator=(const GilReleaseGuard&) BSLS_KEYWORD_DELETED;

  public:
    // CREATORS
    GilReleaseGuard();
    // Construct this guard, releasing the GIL.

    ~GilReleaseGuard();
    // Destroy this guard, reacquiring the GIL.
};

// ===========================================================================
//                              INLINE DEFINITIONS
// ===========================================================================

inline GilReleaseGuard::GilReleaseGuard()
: d_saved_thread_state(PyEval_SaveThread())
{
}

inline GilReleaseGuard::~GilReleaseGuard()
{
    PyEval_RestoreThread(d_saved_thread_state);
}

}  // namespace pybmq
}  // namespace BloombergLP

#endif
