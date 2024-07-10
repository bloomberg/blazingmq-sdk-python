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

#include <pybmq_session.h>

#include <pybmq_gilreleaseguard.h>
#include <pybmq_messageutils.h>
#include <pybmq_mocksession.h>
#include <pybmq_refutils.h>
#include <pybmq_sessioneventhandler.h>

#include <bsl_memory.h>
#include <bsl_sstream.h>
#include <bsl_stdexcept.h>
#include <bsl_string.h>
#include <bslma_default.h>
#include <bslma_managedptr.h>
#include <bslmt_readerwriterlockassert.h>
#include <bslmt_readlockguard.h>
#include <bslmt_writelockguard.h>

#include <bmqt_queueflags.h>
#include <bmqt_queueoptions.h>
#include <bmqt_resultcode.h>
#include <bmqt_sessionoptions.h>

namespace BloombergLP {
namespace pybmq {
static const char* const SESSION_STOPPED = "Method called after session was stopped";
static const char* const QUEUE_NOT_OPENED = "Queue not opened";

namespace {

class GenericError : public bsl::runtime_error
{
  public:
    GenericError(const char* msg)
    : bsl::runtime_error(msg)
    {
    }

    GenericError(const std::string& msg)
    : bsl::runtime_error(msg)
    {
    }
};

class BrokerTimeoutError : public bsl::runtime_error
{
  public:
    BrokerTimeoutError(const char* msg)
    : bsl::runtime_error(msg)
    {
    }

    BrokerTimeoutError(const std::string& msg)
    : bsl::runtime_error(msg)
    {
    }
};

}  // namespace

Session::Session(
        PyObject* py_session_event_callback,
        PyObject* py_message_event_callback,
        PyObject* py_ack_event_callback,
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
        bsl::shared_ptr<bmqa::ManualHostHealthMonitor> fake_host_health_monitor_sp,
        PyObject* error,
        PyObject* broker_timeout_error,
        PyObject* mock)
: d_started_lock()
, d_started(false)
, d_message_compression_type(bmqt::CompressionAlgorithmType::e_NONE)
, d_error(error)
, d_broker_timeout_error(broker_timeout_error)
, d_session_mp()
{
    bsl::shared_ptr<bmqpi::HostHealthMonitor> host_health_monitor_sp;

    if (fake_host_health_monitor_sp) {
        host_health_monitor_sp = fake_host_health_monitor_sp;
    } else if (monitor_host_health) {
    }

    if (message_compression_type
                < bmqt::CompressionAlgorithmType::k_LOWEST_SUPPORTED_TYPE
        || message_compression_type
                   > bmqt::CompressionAlgorithmType::k_HIGHEST_SUPPORTED_TYPE)
    {
        PyErr_SetString(PyExc_ValueError, "Invalid message compression type");
        throw bsl::runtime_error("propagating Python error");
    }

    d_message_compression_type = message_compression_type;
    {
        pybmq::GilReleaseGuard guard;
        bmqt::SessionOptions options;
        options.setBrokerUri(broker_uri)
                .setProcessNameOverride(script_name)
                .setHostHealthMonitor(host_health_monitor_sp);

        if (num_processing_threads.has_value()) {
            options.setNumProcessingThreads(num_processing_threads.value());
        }

        if (blob_buffer_size.has_value()) {
            options.setBlobBufferSize(blob_buffer_size.value());
        }

        if (channel_high_watermark.has_value()) {
            options.setChannelHighWatermark(channel_high_watermark.value());
        }

        if (event_queue_watermarks.has_value()) {
            options.configureEventQueue(
                    event_queue_watermarks.value().first,
                    event_queue_watermarks.value().second);
        }

        if (stats_dump_interval != bsls::TimeInterval()) {
            options.setStatsDumpInterval(stats_dump_interval);
        }

        if (connect_timeout != bsls::TimeInterval()) {
            options.setConnectTimeout(connect_timeout);
        }

        if (disconnect_timeout != bsls::TimeInterval()) {
            options.setDisconnectTimeout(disconnect_timeout);
        }

        if (open_queue_timeout != bsls::TimeInterval()) {
            options.setOpenQueueTimeout(open_queue_timeout);
        }

        if (configure_queue_timeout != bsls::TimeInterval()) {
            options.setConfigureQueueTimeout(configure_queue_timeout);
        }

        if (close_queue_timeout != bsls::TimeInterval()) {
            options.setCloseQueueTimeout(close_queue_timeout);
        }

        bslma::ManagedPtr<bmqa::SessionEventHandler> handler(
                new pybmq::SessionEventHandler(
                        py_session_event_callback,
                        py_message_event_callback,
                        py_ack_event_callback));
        if (mock == Py_None) {
            d_session_mp = bslma::ManagedPtr<bmqa::AbstractSession>(
                    new bmqa::Session(handler, options));
        } else {
            d_session_mp = bslma::ManagedPtr<bmqa::AbstractSession>(
                    new pybmq::MockSession(mock, handler, options));
        }
    }
    Py_INCREF(d_error);
    Py_INCREF(d_broker_timeout_error);
}

Session::~Session()
{
    Py_DECREF(d_broker_timeout_error);
    Py_DECREF(d_error);
    BSLS_ASSERT(!d_started);
    pybmq::GilReleaseGuard gil_release_guard;
    d_session_mp.reset();
}

PyObject*
Session::start(const bsls::TimeInterval& timeout)
{
    bmqt::GenericResult::Enum rc;
    {
        pybmq::GilReleaseGuard guard;
        rc = (bmqt::GenericResult::Enum)d_session_mp->start(timeout);
    }
    if (rc == bmqt::GenericResult::e_SUCCESS) {
        d_started = true;
        Py_RETURN_NONE;
    }
    PyObject* error_class =
            (rc == bmqt::GenericResult::e_TIMEOUT) ? d_broker_timeout_error : d_error;
    bsl::ostringstream oss;
    oss << "Failed to start session: " << rc;
    bsl::string error_message = oss.str();
    PyErr_SetString(error_class, error_message.c_str());
    return NULL;
}

PyObject*
Session::stop(bool warn_if_started)
{
    bool was_started;
    bool generate_warning;
    {
        pybmq::GilReleaseGuard gil_release_guard;
        {
            bslmt::WriteLockGuard<bslmt::ReaderWriterLock> guard(&d_started_lock);
            was_started = d_started;
            generate_warning = d_started && warn_if_started;
            d_started = false;
        }
        if (was_started) {
            // Note: Neither the GIL nor d_started_lock may be held here.
            d_session_mp->stop();
        }
    }

    if (generate_warning) {
        bsl::ostringstream oss;
        oss << "stop() not invoked before destruction of Session<" << this
            << "> object";
        if (PyErr_WarnEx(PyExc_UserWarning, oss.str().c_str(), 1) == -1) {
            // Ensure that we raise if the user decides to set warnings as errors.
            return NULL;
        }
    }
    Py_RETURN_NONE;
}

PyObject*
Session::open_queue_sync(
        const char* queue_uri,
        bool read,
        bool write,
        bsl::optional<int> consumer_priority,
        bsl::optional<int> max_unconfirmed_messages,
        bsl::optional<int> max_unconfirmed_bytes,
        bsl::optional<bool> suspends_on_bad_host_health,
        const bsls::TimeInterval& timeout)
{
    try {
        pybmq::GilReleaseGuard gil_release_guard;
        bslmt::ReadLockGuard<bslmt::ReaderWriterLock> guard(&d_started_lock);

        if (!d_started) {
            throw GenericError(SESSION_STOPPED);
        }

        bsls::Types::Uint64 flags = 0;
        if (read) {
            bmqt::QueueFlagsUtil::setReader(&flags);
        }
        if (write) {
            bmqt::QueueFlagsUtil::setWriter(&flags);
        }

        bmqa::QueueId dummy;

        bmqt::QueueOptions options;

        if (consumer_priority) {
            options.setConsumerPriority(*consumer_priority);
        }

        if (max_unconfirmed_messages) {
            options.setMaxUnconfirmedMessages(*max_unconfirmed_messages);
        }

        if (max_unconfirmed_bytes) {
            options.setMaxUnconfirmedBytes(*max_unconfirmed_bytes);
        }

        if (suspends_on_bad_host_health) {
            options.setSuspendsOnBadHostHealth(*suspends_on_bad_host_health);
        }

        bmqa::OpenQueueStatus oqs;
        oqs = d_session_mp->openQueueSync(
                &dummy,
                bmqt::Uri(queue_uri),
                flags,
                options,
                timeout);
        if (oqs.result()) {
            bsl::ostringstream oss;
            oss << "Failed to open " << queue_uri << " queue: " << oqs.result() << ": "
                << oqs.errorDescription();
            if (oqs.result() == bmqt::OpenQueueResult::e_TIMEOUT) {
                throw BrokerTimeoutError(oss.str());
            }
            throw GenericError(oss.str());
        }
    } catch (const GenericError& exc) {
        PyErr_SetString(d_error, exc.what());
        return NULL;
    } catch (const BrokerTimeoutError& exc) {
        PyErr_SetString(d_broker_timeout_error, exc.what());
        return NULL;
    }

    Py_RETURN_NONE;
}

PyObject*
Session::configure_queue_sync(
        const char* queue_uri,
        bsl::optional<int> consumer_priority,
        bsl::optional<int> max_unconfirmed_messages,
        bsl::optional<int> max_unconfirmed_bytes,
        bsl::optional<bool> suspends_on_bad_host_health,
        const bsls::TimeInterval& timeout)
{
    try {
        pybmq::GilReleaseGuard gil_release_guard;
        bslmt::ReadLockGuard<bslmt::ReaderWriterLock> guard(&d_started_lock);

        if (!d_started) {
            throw GenericError(SESSION_STOPPED);
        }

        bmqa::QueueId queue_id;
        if (d_session_mp->getQueueId(&queue_id, bmqt::Uri(queue_uri))) {
            throw GenericError(QUEUE_NOT_OPENED);
        }

        bmqt::QueueOptions options;

        if (consumer_priority) {
            options.setConsumerPriority(*consumer_priority);
        }

        if (max_unconfirmed_messages) {
            options.setMaxUnconfirmedMessages(*max_unconfirmed_messages);
        }

        if (max_unconfirmed_bytes) {
            options.setMaxUnconfirmedBytes(*max_unconfirmed_bytes);
        }

        if (suspends_on_bad_host_health) {
            options.setSuspendsOnBadHostHealth(*suspends_on_bad_host_health);
        }

        bmqa::ConfigureQueueStatus cqs;
        cqs = d_session_mp->configureQueueSync(&queue_id, options, timeout);

        if (cqs.result()) {
            bsl::ostringstream oss;
            oss << "Failed to configure " << queue_uri << " queue: " << cqs.result()
                << ": " << cqs.errorDescription();
            if (cqs.result() == bmqt::ConfigureQueueResult::e_TIMEOUT) {
                throw BrokerTimeoutError(oss.str());
            }
            throw GenericError(oss.str());
        }
    } catch (const GenericError& exc) {
        PyErr_SetString(d_error, exc.what());
        return NULL;
    } catch (const BrokerTimeoutError& exc) {
        PyErr_SetString(d_broker_timeout_error, exc.what());
        return NULL;
    }

    Py_RETURN_NONE;
}

PyObject*
Session::close_queue_sync(const char* queue_uri, const bsls::TimeInterval& timeout)
{
    try {
        pybmq::GilReleaseGuard gil_release_guard;
        bslmt::ReadLockGuard<bslmt::ReaderWriterLock> guard(&d_started_lock);

        if (!d_started) {
            throw GenericError(SESSION_STOPPED);
        }

        bmqa::QueueId queue_id;
        if (d_session_mp->getQueueId(&queue_id, bmqt::Uri(queue_uri))) {
            throw GenericError(QUEUE_NOT_OPENED);
        }

        bmqa::CloseQueueStatus cqs;
        cqs = d_session_mp->closeQueueSync(&queue_id, timeout);

        if (cqs.result()) {
            bsl::ostringstream oss;
            oss << "Failed to close " << queue_uri << " queue: " << cqs.result() << ": "
                << cqs.errorDescription();
            if (cqs.result() == bmqt::CloseQueueResult::e_TIMEOUT) {
                throw BrokerTimeoutError(oss.str());
            }
            throw GenericError(oss.str());
        }
    } catch (const GenericError& exc) {
        PyErr_SetString(d_error, exc.what());
        return NULL;
    } catch (const BrokerTimeoutError& exc) {
        PyErr_SetString(d_broker_timeout_error, exc.what());
        return NULL;
    }

    Py_RETURN_NONE;
}

PyObject*
Session::get_queue_options(const char* queue_uri)
{
    int max_unconfirmed_messages;
    int max_unconfirmed_bytes;
    int consumer_priority;
    bool suspends_on_bad_host_health;

    try {
        pybmq::GilReleaseGuard gil_release_guard;
        bslmt::ReadLockGuard<bslmt::ReaderWriterLock> guard(&d_started_lock);

        if (!d_started) {
            throw GenericError(SESSION_STOPPED);
        }

        bmqa::QueueId queue_id;
        if (d_session_mp->getQueueId(&queue_id, bmqt::Uri(queue_uri))) {
            throw GenericError(QUEUE_NOT_OPENED);
        }

        const bmqt::QueueOptions& options = queue_id.options();
        max_unconfirmed_messages = options.maxUnconfirmedMessages();
        max_unconfirmed_bytes = options.maxUnconfirmedBytes();
        consumer_priority = options.consumerPriority();
        suspends_on_bad_host_health = options.suspendsOnBadHostHealth();
    } catch (const GenericError& exc) {
        PyErr_SetString(d_error, exc.what());
        return NULL;
    }

    return Py_BuildValue(
            "i i i O",
            max_unconfirmed_messages,
            max_unconfirmed_bytes,
            consumer_priority,
            suspends_on_bad_host_health ? Py_True : Py_False);
}

PyObject*
Session::post(
        const char* queue_uri,
        const char* payload,
        size_t payload_length,
        PyObject* properties,
        PyObject* on_ack)
{
    bslma::ManagedPtr<PyObject> managed_on_ack;
    if (on_ack != Py_None) {
        managed_on_ack = RefUtils::toManagedPtr(RefUtils::ref(on_ack));
    }

    bmqa::MessageProperties c_properties;
    if (properties != Py_None) {
        d_session_mp->loadMessageProperties(&c_properties);
        if (!pybmq::MessageUtils::load_message_properties(&c_properties, properties)) {
            return NULL;
        }
    }

    try {
        pybmq::GilReleaseGuard gil_release_guard;
        bslmt::ReadLockGuard<bslmt::ReaderWriterLock> guard(&d_started_lock);

        if (!d_started) {
            throw GenericError(SESSION_STOPPED);
        }

        bmqa::QueueId queue_id;
        if (d_session_mp->getQueueId(&queue_id, bmqt::Uri(queue_uri))) {
            throw GenericError(QUEUE_NOT_OPENED);
        }

        bmqa::MessageEventBuilder builder;
        d_session_mp->loadMessageEventBuilder(&builder);

        bmqa::Message& message = builder.startMessage();

        message.setDataRef(payload, payload_length);

        if (properties != Py_None) {
            message.setPropertiesRef(&c_properties);
        }

        if (on_ack != Py_None) {
            message.setCorrelationId(bmqt::CorrelationId(on_ack));
        }

        message.setCompressionAlgorithmType(d_message_compression_type);

        bmqt::EventBuilderResult::Enum builder_rc = builder.packMessage(queue_id);
        if (builder_rc) {
            bsl::ostringstream oss;
            oss << "Failed to construct message: " << builder_rc;
            throw GenericError(oss.str());
        }

        bmqt::MessageGUID c_guid = builder.currentMessage().messageGUID();
        unsigned char guid[bmqt::MessageGUID::e_SIZE_BINARY];
        c_guid.toBinary(guid);
        PyObject* python_guid = PyBytes_FromStringAndSize(
                // Cython converts between unsigned char and char when
                // converting between Python `bytes` and C++ `(unsigned) char`,
                // but we need to do this ourselves here.
                reinterpret_cast<char*>(guid),
                bmqt::MessageGUID::e_SIZE_BINARY);

        const bmqa::MessageEvent& messageEvent = builder.messageEvent();
        bmqt::PostResult::Enum post_rc =
                (bmqt::PostResult::Enum)d_session_mp->post(messageEvent);
        if (post_rc) {
            bsl::ostringstream oss;
            oss << "Failed to post message to " << queue_uri << " queue: " << post_rc;
            throw GenericError(oss.str());
        }
        // We have a successful post and the SDK now owns the `on_ack` callback object
        // so release our reference without a DECREF.
        managed_on_ack.release();

        return python_guid;
    } catch (const GenericError& exc) {
        PyErr_SetString(d_error, exc.what());
        return NULL;
    }

    Py_RETURN_NONE;
}

PyObject*
Session::confirm(const char* queue_uri, const unsigned char* guid, size_t guid_length)
{
    try {
        pybmq::GilReleaseGuard gil_release_guard;
        bslmt::ReadLockGuard<bslmt::ReaderWriterLock> guard(&d_started_lock);

        if (!d_started) {
            throw GenericError(SESSION_STOPPED);
        }

        bmqa::QueueId queue_id;
        if (d_session_mp->getQueueId(&queue_id, bmqt::Uri(queue_uri))) {
            throw GenericError(QUEUE_NOT_OPENED);
        }

        if (!queue_id.isValid()) {
            bsl::ostringstream oss;
            oss << "Attempting to confirm message on a closing queue. Please ensure "
                   "that you are invoking configure with 0 max unconfirmed messages "
                   "before closing the queue<"
                << queue_uri << ">";
            throw GenericError(oss.str());
        }

        bmqt::MessageGUID c_guid;
        if (guid_length != bmqt::MessageGUID::e_SIZE_BINARY) {
            throw GenericError("Invalid GUID provided");
        }
        c_guid.fromBinary(guid);

        bmqt::GenericResult::Enum confirm_rc =
                (bmqt::GenericResult::Enum)d_session_mp->confirmMessage(
                        bmqa::MessageConfirmationCookie(queue_id, c_guid));
        if (confirm_rc) {
            bsl::ostringstream oss;
            oss << "Failed to confirm message [" << c_guid << "]: " << confirm_rc;
            throw GenericError(oss.str());
        }
    } catch (const GenericError& exc) {
        PyErr_SetString(d_error, exc.what());
        return NULL;
    }

    Py_RETURN_NONE;
}

}  // namespace pybmq
}  // namespace BloombergLP
