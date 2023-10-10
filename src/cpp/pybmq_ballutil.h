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

#ifndef PYBMQ_BALLUTIL_H
#define PYBMQ_BALLUTIL_H

#define PY_SSIZE_T_CLEAN
#include <Python.h>

namespace BloombergLP {
namespace pybmq {

struct BallUtil
{
    // This utility provides functions for creating and destroying a BALL
    // singleton with an observer that redirects to the Python logging module.

    // TYPES
    typedef PyObject* (*LogEntryCallback)(
            const char* name,
            int level,
            const char* file,
            int line,
            const char* msg);
    // When initializing the BALL singleton, a callback function must be
    // provided that will be called once per log record.

    // CLASS METHODS
    static PyObject* initBallSingleton(LogEntryCallback cb, PyObject* context);
    // Given a callback function, create the BALL singleton and set up an
    // observer that calls that callback for each log record.

    static PyObject* shutDownBallSingleton();
    // Destroy the BALL singleton created by 'initBallSingleton'.
};

}  // namespace pybmq
}  // namespace BloombergLP

#endif
