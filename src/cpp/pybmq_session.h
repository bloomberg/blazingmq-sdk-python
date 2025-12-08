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

#ifndef INCLUDED_PYBMQ_SESSION
#define INCLUDED_PYBMQ_SESSION

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <bmqa_abstractsession.h>
#include <bmqa_manualhosthealthmonitor.h>
#include <bmqt_authncredential.h>
#include <bmqt_compressionalgorithmtype.h>

#include <bsl_memory.h>
#include <bsl_optional.h>
#include <bslma_managedptr.h>
#include <bslmt_readerwriterlock.h>
#include <bsls_timeinterval.h>

namespace BloombergLP {
namespace pybmq {

class Session
{
  private:
    // DATA
    bslmt::ReaderWriterLock d_started_lock;
    bool d_started;
    bmqt::CompressionAlgorithmType::Enum d_message_compression_type;
    PyObject* d_error;
    PyObject* d_broker_timeout_error;
    bslma::ManagedPtr<bmqa::AbstractSession> d_session_mp;

    // NOT IMPLEMENTED
    Session(const Session&);
    Session& operator=(const Session&);

    // TODO: Remove this once it's added in SessionOptions
    typedef bsl::function<bsl::optional<bmqt::AuthnCredential>(bsl::ostream& error)>
            AuthnCredentialCb;

  public:
    Session(PyObject* py_session_event_callback,
            PyObject* py_message_event_callback,
            PyObject* py_ack_event_callback,
            PyObject* fake_authn_credential_cb,
            const char* broker_uri,
            const char* script_name,
            bmqt::CompressionAlgorithmType::Enum message_compression_type,
            bsl::optional<int> num_processing_threads,
            bsl::optional<int> blob_buffer_size,
            bsl::optional<int> channel_high_watermark,
            bsl::optional<bsl::pair<int, int> > event_queue_watermarks,
            const bsls::TimeInterval& stats_dump_interval,
            const bsls::TimeInterval& connect_timeout,
            const bsls::TimeInterval& disconnect_timeout,
            const bsls::TimeInterval& open_queue_timeout,
            const bsls::TimeInterval& configure_queue_timeout,
            const bsls::TimeInterval& close_queue_timeout,
            bool monitor_host_health,
            bsl::shared_ptr<bmqa::ManualHostHealthMonitor> fake_host_health_monitor,
            PyObject* d_error,
            PyObject* d_broker_timeout_error,
            PyObject* mock);

    ~Session();

    PyObject* start(const bsls::TimeInterval& timeout);
    PyObject* stop(bool warn_if_started);

    PyObject* open_queue_sync(
            const char* queue_uri,
            bool read,
            bool write,
            bsl::optional<int> consumer_priority,
            bsl::optional<int> max_unconfirmed_messages,
            bsl::optional<int> max_unconfirmed_bytes,
            bsl::optional<bool> suspends_on_bad_host_health,
            const bsls::TimeInterval& timeout);

    PyObject* configure_queue_sync(
            const char* queue_uri,
            bsl::optional<int> consumer_priority,
            bsl::optional<int> max_unconfirmed_messages,
            bsl::optional<int> max_unconfirmed_bytes,
            bsl::optional<bool> suspends_on_bad_host_health,
            const bsls::TimeInterval& timeout);

    PyObject*
    close_queue_sync(const char* queue_uri, const bsls::TimeInterval& timeout);

    PyObject* get_queue_options(const char* queue_uri);

    PyObject*
    post(const char* queue_uri,
         const char* payload,
         size_t payload_length,
         PyObject* properties,
         PyObject* on_ack);

    PyObject*
    confirm(const char* queue_uri, const unsigned char* guid, size_t guid_length);
};

}  // namespace pybmq
}  // namespace BloombergLP

#endif
