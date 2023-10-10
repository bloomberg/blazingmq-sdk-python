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

#ifndef INCLUDED_PYBMQ_SESSIONEVENTHANDLER
#define INCLUDED_PYBMQ_SESSIONEVENTHANDLER

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <bmqa_messageevent.h>
#include <bmqa_session.h>
#include <bmqa_sessionevent.h>

#include <bsls_keyword.h>

namespace BloombergLP {
namespace pybmq {

class SessionEventHandler : public bmqa::SessionEventHandler
{
  private:
    PyObject* d_py_session_event_callback;
    PyObject* d_py_message_event_callback;
    PyObject* d_py_ack_event_callback;

  public:
    SessionEventHandler(
            PyObject* py_session_event_callback,
            PyObject* py_message_event_callback,
            PyObject* py_ack_event_callback);

    ~SessionEventHandler();

    void onSessionEvent(const bmqa::SessionEvent& event) BSLS_KEYWORD_OVERRIDE;
    void onMessageEvent(const bmqa::MessageEvent& event) BSLS_KEYWORD_OVERRIDE;
};

}  // namespace pybmq
}  // namespace BloombergLP

#endif
