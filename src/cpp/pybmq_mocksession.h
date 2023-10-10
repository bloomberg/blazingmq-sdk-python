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

#ifndef INCLUDED_PYBMQ_MOCKSESSION
#define INCLUDED_PYBMQ_MOCKSESSION

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <bmqa_abstractsession.h>
#include <bmqa_closequeuestatus.h>
#include <bmqa_configurequeuestatus.h>
#include <bmqa_messageevent.h>
#include <bmqa_messageiterator.h>
#include <bmqa_messageproperties.h>
#include <bmqa_openqueuestatus.h>
#include <bmqa_session.h>
#include <bmqa_sessionevent.h>

#include <bmqt_correlationid.h>
#include <bmqt_sessionoptions.h>

#include <bmqa_mocksession.h>

#include <bsl_string.h>
#include <bsls_keyword.h>

namespace BloombergLP {
namespace pybmq {

class MockSession : public bmqa::AbstractSession
{
    // Concrete implementation of an bmqa::AbstractSession that delegates calls
    // to a unittest.mock, marshalling parameters and return values between
    // Python and C++ as needed.

  private:
    // DATA
    PyObject* d_mock;
    bmqa::MockSession d_mock_session;

    // NOT IMPLEMENTED
    MockSession(const MockSession&);
    MockSession& operator=(const MockSession&);

  public:
    // CREATORS
    MockSession(
            PyObject* mock,
            bslma::ManagedPtr<bmqa::SessionEventHandler> eventHandler,
            const bmqt::SessionOptions& options);

    ~MockSession();
    // Destroy this object.

    // Session management
    ///----------------

    int start(const bsls::TimeInterval& timeout = bsls::TimeInterval())
            BSLS_KEYWORD_OVERRIDE;
    // Call `start()` on the mock and propagate its return value.

    int startAsync(const bsls::TimeInterval& timeout = bsls::TimeInterval())
            BSLS_KEYWORD_OVERRIDE;
    // Throw an exception if called.

    void stop() BSLS_KEYWORD_OVERRIDE;
    // Throw an exception if called.

    void stopAsync() BSLS_KEYWORD_OVERRIDE;
    // Call `stopAsync()` on the mock and propagate its return value.

    void finalizeStop() BSLS_KEYWORD_OVERRIDE;
    // Call `finalizeStop()` on the mock and propagate its return value.

    void
    loadMessageEventBuilder(bmqa::MessageEventBuilder* builder) BSLS_KEYWORD_OVERRIDE;

    void
    loadConfirmEventBuilder(bmqa::ConfirmEventBuilder* builder) BSLS_KEYWORD_OVERRIDE;

    void loadMessageProperties(bmqa::MessageProperties* buffer) BSLS_KEYWORD_OVERRIDE;

    /// Queue management
    ///----------------
    int getQueueId(bmqa::QueueId* queueId, const bmqt::Uri& uri) BSLS_KEYWORD_OVERRIDE;

    int getQueueId(bmqa::QueueId* queueId, const bmqt::CorrelationId& correlationId)
            BSLS_KEYWORD_OVERRIDE;

    int openQueue(
            bmqa::QueueId* queueId,
            const bmqt::Uri& uri,
            bsls::Types::Uint64 flags,
            const bmqt::QueueOptions& options = bmqt::QueueOptions(),
            const bsls::TimeInterval& timeout = bsls::TimeInterval())
            BSLS_KEYWORD_OVERRIDE;

    int openQueueAsync(
            bmqa::QueueId* queueId,
            const bmqt::Uri& uri,
            bsls::Types::Uint64 flags,
            const bmqt::QueueOptions& options = bmqt::QueueOptions(),
            const bsls::TimeInterval& timeout = bsls::TimeInterval())
            BSLS_KEYWORD_OVERRIDE;

    void openQueueAsync(
            bmqa::QueueId* queueId,
            const bmqt::Uri& uri,
            bsls::Types::Uint64 flags,
            const OpenQueueCallback& callback,
            const bmqt::QueueOptions& options = bmqt::QueueOptions(),
            const bsls::TimeInterval& timeout = bsls::TimeInterval())
            BSLS_KEYWORD_OVERRIDE;

    bmqa::OpenQueueStatus openQueueSync(
            bmqa::QueueId* queueId,
            const bmqt::Uri& uri,
            bsls::Types::Uint64 flags,
            const bmqt::QueueOptions& options = bmqt::QueueOptions(),
            const bsls::TimeInterval& timeout = bsls::TimeInterval())
            BSLS_KEYWORD_OVERRIDE;

    int configureQueue(
            bmqa::QueueId* queueId,
            const bmqt::QueueOptions& options,
            const bsls::TimeInterval& timeout = bsls::TimeInterval())
            BSLS_KEYWORD_OVERRIDE;

    int configureQueueAsync(
            bmqa::QueueId* queueId,
            const bmqt::QueueOptions& options,
            const bsls::TimeInterval& timeout = bsls::TimeInterval())
            BSLS_KEYWORD_OVERRIDE;
    void configureQueueAsync(
            bmqa::QueueId* queueId,
            const bmqt::QueueOptions& options,
            const ConfigureQueueCallback& callback,
            const bsls::TimeInterval& timeout = bsls::TimeInterval())
            BSLS_KEYWORD_OVERRIDE;

    bmqa::ConfigureQueueStatus configureQueueSync(
            bmqa::QueueId* queueId,
            const bmqt::QueueOptions& options,
            const bsls::TimeInterval& timeout = bsls::TimeInterval())
            BSLS_KEYWORD_OVERRIDE;

    int closeQueue(
            bmqa::QueueId* queueId,
            const bsls::TimeInterval& timeout = bsls::TimeInterval())
            BSLS_KEYWORD_OVERRIDE;

    int closeQueueAsync(
            bmqa::QueueId* queueId,
            const bsls::TimeInterval& timeout = bsls::TimeInterval())
            BSLS_KEYWORD_OVERRIDE;

    void closeQueueAsync(
            bmqa::QueueId* queueId,
            const CloseQueueCallback& callback,
            const bsls::TimeInterval& timeout = bsls::TimeInterval())
            BSLS_KEYWORD_OVERRIDE;

    bmqa::CloseQueueStatus closeQueueSync(
            bmqa::QueueId* queueId,
            const bsls::TimeInterval& timeout = bsls::TimeInterval())
            BSLS_KEYWORD_OVERRIDE;

    /// Queue manipulation
    ///------------------
    bmqa::Event nextEvent(const bsls::TimeInterval& timeout = bsls::TimeInterval())
            BSLS_KEYWORD_OVERRIDE;

    int post(const bmqa::MessageEvent& event) BSLS_KEYWORD_OVERRIDE;

    int confirmMessage(const bmqa::Message& message) BSLS_KEYWORD_OVERRIDE;

    int
    confirmMessage(const bmqa::MessageConfirmationCookie& cookie) BSLS_KEYWORD_OVERRIDE;

    int confirmMessages(bmqa::ConfirmEventBuilder* builder) BSLS_KEYWORD_OVERRIDE;

    /// Debugging related
    ///-----------------
    int configureMessageDumping(const bslstl::StringRef& command) BSLS_KEYWORD_OVERRIDE;
};
}  // namespace pybmq
}  // namespace BloombergLP
#endif
