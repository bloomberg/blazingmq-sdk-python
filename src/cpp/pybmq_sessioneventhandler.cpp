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

#include <pybmq_sessioneventhandler.h>

#include <pybmq_gilacquireguard.h>
#include <pybmq_messageutils.h>
#include <pybmq_refutils.h>

#include <bmqa_message.h>
#include <bmqa_messageiterator.h>
#include <bmqt_messageeventtype.h>
#include <bmqt_resultcode.h>
#include <bmqt_sessioneventtype.h>

#include <bsl_string.h>
#include <bslma_managedptr.h>

namespace BloombergLP {
namespace pybmq {

SessionEventHandler::SessionEventHandler(
        PyObject* py_session_event_callback,
        PyObject* py_message_event_callback,
        PyObject* py_ack_event_callback)
: d_py_session_event_callback(py_session_event_callback)
, d_py_message_event_callback(py_message_event_callback)
, d_py_ack_event_callback(py_ack_event_callback)
{
    GilAcquireGuard guard;
    Py_INCREF(d_py_session_event_callback);
    Py_INCREF(d_py_message_event_callback);
    Py_INCREF(d_py_ack_event_callback);
}

SessionEventHandler::~SessionEventHandler()
{
    GilAcquireGuard guard;
    Py_DECREF(d_py_ack_event_callback);
    Py_DECREF(d_py_message_event_callback);
    Py_DECREF(d_py_session_event_callback);
}

void
SessionEventHandler::onSessionEvent(const bmqa::SessionEvent& event)
{
    GilAcquireGuard guard;
    bsl::string uri;

    if (event.type() == bmqt::SessionEventType::e_QUEUE_REOPEN_RESULT
        || event.type() == bmqt::SessionEventType::e_QUEUE_SUSPENDED
        || event.type() == bmqt::SessionEventType::e_QUEUE_RESUMED)
    {
        uri = event.queueId().uri().asString();
    }

    bslma::ManagedPtr<PyObject> rv = RefUtils::toManagedPtr(PyObject_CallFunction(
            d_py_session_event_callback,
            "(N (i N i N s#))",
            PyBytes_FromStringAndSize(
                    event.errorDescription().c_str(),
                    event.errorDescription().length()),
            event.type(),
            PyBytes_FromString(bmqt::SessionEventType::toAscii(event.type())),
            event.statusCode(),
            PyBytes_FromString(bmqt::GenericResult::toAscii(
                    static_cast<bmqt::GenericResult::Enum>(event.statusCode()))),
            uri.c_str(),
            uri.length()));
    if (!rv) {
        PyErr_Print();
    }
}

void
SessionEventHandler::onMessageEvent(const bmqa::MessageEvent& event)
{
    GilAcquireGuard guard;
    PyObject* callback;
    PyObject* py_event;

    if (event.type() == bmqt::MessageEventType::e_PUSH) {
        callback = d_py_message_event_callback;
        py_event = MessageUtils::get_messages(event, d_py_session_event_callback);
    } else if (event.type() == bmqt::MessageEventType::e_ACK) {
        callback = d_py_ack_event_callback;
        py_event = MessageUtils::get_acks(event);
    } else {
        bsl::ostringstream oss;
        oss << "Received an unexpected message event of type " << (int)event.type()
            << " (" << event.type() << ")";
        callback = d_py_session_event_callback;
        py_event = PyBytes_FromString(oss.str().c_str());
    }
    bslma::ManagedPtr<PyObject> rv =
            RefUtils::toManagedPtr(PyObject_CallFunction(callback, "(N)", py_event));
    if (!rv) {
        PyErr_Print();
    }
}

}  // namespace pybmq
}  // namespace BloombergLP
