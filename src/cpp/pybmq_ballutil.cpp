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

#include <pybmq_ballutil.h>
#include <pybmq_gilacquireguard.h>
#include <pybmq_refutils.h>

#include <ball_context.h>
#include <ball_log.h>
#include <ball_loggermanager.h>
#include <ball_observeradapter.h>
#include <ball_record.h>
#include <ball_severity.h>
#include <bsl_string.h>
#include <bslma_managedptr.h>
#include <bsls_keyword.h>

#include <cstdlib>

namespace BloombergLP {
namespace pybmq {

namespace {  // unnamed

int
ball_severity_to_python_level(int severity)
{
    // Documented in the "logging" module's public documentation.
    enum {
        FATAL = 50,
        ERROR = 40,
        WARN = 30,
        INFO = 20,
        DEBUG = 10,
    };

    if (severity > ball::Severity::e_INFO) return DEBUG;
    if (severity > ball::Severity::e_WARN) return INFO;
    if (severity > ball::Severity::e_ERROR) return WARN;
    if (severity > ball::Severity::e_FATAL) return ERROR;
    return FATAL;
}

class Observer : public ball::ObserverAdapter
{
  private:
    // DATA
    BallUtil::LogEntryCallback d_cb;
    bslma::ManagedPtr<PyObject> d_context;

    // NOT IMPLEMENTED
    Observer(const Observer&) BSLS_KEYWORD_DELETED;
    Observer& operator=(const Observer&) BSLS_KEYWORD_DELETED;

  public:
    // CREATORS
    Observer(BallUtil::LogEntryCallback cb, PyObject* context);
    virtual ~Observer()
    {
    }

    // MANIPULATORS
    void publish(const ball::Record&, const ball::Context&);
};

// CREATORS
Observer::Observer(BallUtil::LogEntryCallback cb, PyObject* context)
: d_cb(cb)
{
    d_context = RefUtils::toManagedPtr(RefUtils::ref(context));
}

// MANIPULATORS
void
Observer::publish(const ball::Record& record, const ball::Context&)
{
    bsl::string name = bsl::string("blazingmq.") + record.fixedFields().category();

    GilAcquireGuard guard;
    bslma::ManagedPtr<PyObject> ret = RefUtils::toManagedPtr(
            d_cb(name.c_str(),
                 ball_severity_to_python_level(record.fixedFields().severity()),
                 record.fixedFields().fileName(),
                 record.fixedFields().lineNumber(),
                 record.fixedFields().message()));

    if (!ret) {
        PyErr_WriteUnraisable(d_context.get());
    }
}

}  // unnamed namespace

PyObject*
BallUtil::initBallSingleton(BallUtil::LogEntryCallback cb, PyObject* context)
{
    int severity = ball::Severity::INFO;
    if (getenv("_PYBMQ_ENABLE_DIAGNOSTICS")) {
        severity = ball::Severity::DEBUG;
    }

    ball::LoggerManagerConfiguration lmc;
    lmc.setDefaultThresholdLevelsIfValid(
            ball::Severity::OFF,  // cutoff for recording into a log buffer
            severity,  // cutoff for publishing immediately
            ball::Severity::OFF,  // cutoff for publishing this thread's log buffer
            ball::Severity::OFF);  // cutoff for publishing all threads' log buffers

    ball::LoggerManager& manager = ball::LoggerManager::initSingleton(lmc);
    if (manager.registerObserver(bsl::make_shared<Observer>(cb, context), "default")) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to register observer");
        return NULL;
    }

    Py_RETURN_NONE;
}

PyObject*
BallUtil::shutDownBallSingleton()
{
    BALL_LOG_SET_CATEGORY("pybmq_ballutil");
    BALL_LOG_DEBUG << "Shutting down BALL redirection";
    ball::LoggerManager::shutDownSingleton();
    Py_RETURN_NONE;
}

}  // namespace pybmq
}  // namespace BloombergLP
