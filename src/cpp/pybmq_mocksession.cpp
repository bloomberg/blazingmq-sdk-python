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

#include <pybmq_mocksession.h>
#include <pybmq_refutils.h>

#include <pybmq_gilacquireguard.h>
#include <pybmq_messageutils.h>
#include <pybmq_session.h>

#include <bmqa_messageproperties.h>
#include <bmqt_resultcode.h>

#include <bdlbb_blob.h>
#include <bdlbb_blobutil.h>
#include <bdlbb_simpleblobbufferfactory.h>
#include <bsl_stdexcept.h>
#include <bsl_string.h>
#include <bsl_vector.h>
#include <bslma_allocator.h>
#include <bslma_default.h>
#include <bslma_managedptr.h>

namespace BloombergLP {
namespace pybmq {

namespace {

#ifdef BSLS_PLATFORM_CMP_GNU
void
assertNotCalled() __attribute__((noreturn));
#endif

void
assertNotCalled()
{
    throw bsl::runtime_error("mock method not implemented");
}

PyObject*
_Py_DictBuilder_valist(
        const char* const names[],
        const char* const format,
        va_list arguments)
{
    bslma::ManagedPtr<PyObject> pydict = RefUtils::toManagedPtr(PyDict_New());
    if (!pydict) {
        return NULL;
    }
    bslma::ManagedPtr<PyObject> values =
            RefUtils::toManagedPtr(Py_VaBuildValue(format, arguments));
    if (!values) {
        return NULL;
    }
    for (int i = 0; i < PyTuple_Size(values.get()); i++) {
        if (0
            != PyDict_SetItemString(
                    pydict.get(),
                    names[i],
                    PyTuple_GET_ITEM(values.get(), i)))
        {
            return NULL;
        }
    }
    if (PyErr_Occurred()) {
        return NULL;
    }
    return pydict.release().first;
}

PyObject*
_Py_DictBuilder(const char* const names[], const char* const format, ...)
{
    va_list arguments;
    va_start(arguments, format);
    PyObject* return_val = _Py_DictBuilder_valist(names, format, arguments);
    va_end(arguments);
    return return_val;
}

PyObject*
_PyMock_Call(
        PyObject* mock,
        const char* const methodname,
        const char* const names[],
        const char* const format,
        ...)
{
    bslma::ManagedPtr<PyObject> mock_method =
            RefUtils::toManagedPtr(PyObject_GetAttrString(mock, methodname));
    if (!mock_method) {
        return NULL;
    }

    bslma::ManagedPtr<PyObject> args = RefUtils::toManagedPtr(PyTuple_New(0));
    if (!args) {
        return NULL;
    }

    va_list arguments;
    va_start(arguments, format);
    bslma::ManagedPtr<PyObject> keywords =
            RefUtils::toManagedPtr(_Py_DictBuilder_valist(names, format, arguments));
    va_end(arguments);
    if (!keywords) {
        return NULL;
    }

    return PyObject_Call(mock_method.get(), args.get(), keywords.get());
}

void
maybe_emit_messages(PyObject* mock, bmqa::MockSession* mock_session)
{
    if (!PyObject_HasAttrString(mock, "enqueue_messages")) return;

    bslma::ManagedPtr<PyObject> py_message_events =
            RefUtils::toManagedPtr(PyObject_CallMethod(mock, "enqueue_messages", NULL));
    if (!py_message_events) throw bsl::runtime_error("propagating Python error");

    PyObject* py_messages = PyList_GetItem(py_message_events.get(), 0);
    if (!py_messages) throw bsl::runtime_error("propagating Python error");

    bdlbb::SimpleBlobBufferFactory factory(1024);
    bsl::vector<bmqa::MockSessionUtil::PushMessageParams> push_msg_params;

    for (int i = 0; i < PyList_Size(py_messages); ++i) {
        PyObject* item = PyList_GetItem(py_messages, i);
        if (!item) throw bsl::runtime_error("propagating Python error");

        PyObject* py_payload = PyTuple_GetItem(item, 0);
        PyObject* py_guid = PyTuple_GetItem(item, 1);
        PyObject* py_queue_uri = PyTuple_GetItem(item, 2);
        PyObject* py_properties = PyTuple_GetItem(item, 3);
        if (PyErr_Occurred()) throw bsl::runtime_error("propagating Python error");

        bdlbb::Blob payload(&factory);
        const char* c_payload = PyBytes_AsString(py_payload);
        Py_ssize_t c_payload_size = PyBytes_Size(py_payload);
        if (PyErr_Occurred()) throw bsl::runtime_error("propagating Python error");
        bdlbb::BlobUtil::append(&payload, c_payload, c_payload_size);

        bmqt::MessageGUID guid;
        const char* c_guid = PyBytes_AsString(py_guid);
        if (PyErr_Occurred()) throw bsl::runtime_error("propagating Python error");
        if (!bmqt::MessageGUID::isValidHexRepresentation(c_guid)) {
            PyErr_SetString(PyExc_RuntimeError, "Invalid GUID provided");
            throw bsl::runtime_error("propagating Python error");
        }
        guid.fromHex(c_guid);

        bmqa::QueueId queue_id;
        const char* c_queue_uri = PyBytes_AsString(py_queue_uri);
        if (PyErr_Occurred()) throw bsl::runtime_error("propagating Python error");
        if (mock_session->getQueueId(&queue_id, c_queue_uri)) {
            PyErr_SetString(PyExc_RuntimeError, "Failed to get queue");
            throw bsl::runtime_error("propagating Python error");
        }

        bmqa::MessageProperties properties;
        mock_session->loadMessageProperties(&properties);
        if (!pybmq::MessageUtils::load_message_properties(&properties, py_properties)) {
            throw bsl::runtime_error("propagation Python error");
        }

        push_msg_params.emplace_back(payload, queue_id, guid, properties);
    }

    if (PyErr_Occurred()) throw bsl::runtime_error("propagating Python error");

    // Delete the list at index 0, which was processed above to generate a message event
    if (PyList_SetSlice(py_message_events.get(), 0, 1, NULL))
        throw bsl::runtime_error("propagating Python error");

    bslma::Allocator* allocator_p = bslma::Default::defaultAllocator();
    mock_session->enqueueEvent(bmqa::MockSessionUtil::createPushEvent(
            push_msg_params,
            &factory,
            allocator_p));
    if (!mock_session->emitEvent()) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to emit event");
        throw bsl::runtime_error("propagating Python error");
    }
}

void
maybe_emit_acks(PyObject* mock, bmqa::MockSession* mock_session)
{
    if (!PyObject_HasAttrString(mock, "enqueue_acks")) return;

    bslma::ManagedPtr<PyObject> py_ack_events =
            RefUtils::toManagedPtr(PyObject_CallMethod(mock, "enqueue_acks", NULL));
    if (!py_ack_events) throw bsl::runtime_error("propagating Python error");

    PyObject* py_acks = PyList_GetItem(py_ack_events.get(), 0);
    if (!py_acks) throw bsl::runtime_error("propagating Python error");

    bsl::vector<bmqa::MockSessionUtil::AckParams> ack_params;

    for (int i = 0; i < PyList_Size(py_acks); ++i) {
        PyObject* item = PyList_GetItem(py_acks, i);
        if (!item) throw bsl::runtime_error("propagating Python error");

        PyObject* py_status = PyTuple_GetItem(item, 0);
        PyObject* py_guid = PyTuple_GetItem(item, 1);
        PyObject* py_queue_uri = PyTuple_GetItem(item, 2);
        PyObject* py_callback = PyTuple_GetItem(item, 3);
        if (PyErr_Occurred()) throw bsl::runtime_error("propagating Python error");

        bmqt::AckResult::Enum status = (bmqt::AckResult::Enum)PyLong_AsLong(py_status);
        if (PyErr_Occurred()) throw bsl::runtime_error("propagating Python error");

        bmqt::MessageGUID guid;
        const char* c_guid = PyBytes_AsString(py_guid);
        if (PyErr_Occurred()) throw bsl::runtime_error("propagating Python error");
        if (!bmqt::MessageGUID::isValidHexRepresentation(c_guid)) {
            PyErr_SetString(PyExc_RuntimeError, "Invalid GUID provided");
            throw bsl::runtime_error("propagating Python error");
        }
        guid.fromHex(c_guid);

        bmqa::QueueId queue_id;
        const char* c_queue_uri = PyBytes_AsString(py_queue_uri);
        if (PyErr_Occurred()) throw bsl::runtime_error("propagating Python error");
        if (mock_session->getQueueId(&queue_id, c_queue_uri)) {
            PyErr_SetString(PyExc_RuntimeError, "Failed to get queue");
            throw bsl::runtime_error("propagating Python error");
        }

        bmqt::CorrelationId callback(RefUtils::ref(py_callback));

        ack_params.emplace_back(status, callback, guid, queue_id);
    }

    if (PyErr_Occurred()) throw bsl::runtime_error("propagating Python error");

    // Delete the list at index 0, which was processed above to generate an ack event
    if (PyList_SetSlice(py_ack_events.get(), 0, 1, NULL)) {
        throw bsl::runtime_error("propagating Python error");
    }

    bdlbb::SimpleBlobBufferFactory factory(1024);
    bslma::Allocator* allocator_p = bslma::Default::defaultAllocator();
    mock_session->enqueueEvent(
            bmqa::MockSessionUtil::createAckEvent(ack_params, &factory, allocator_p));
    if (!mock_session->emitEvent()) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to emit event");
        throw bsl::runtime_error("propagating Python error");
    }
}

double
time_interval_to_seconds(const bsls::TimeInterval& time_interval)
{
    const double k_S_PER_NS =
            1.0 / static_cast<double>(bdlt::TimeUnitRatio::k_NS_PER_S);

    return time_interval.seconds() + time_interval.nanoseconds() * k_S_PER_NS;
}

}  // namespace

// CREATORS
MockSession::MockSession(
        PyObject* mock,
        bslma::ManagedPtr<bmqa::SessionEventHandler> eventHandler,
        const bmqt::SessionOptions& options)
: d_mock(mock)
, d_mock_session(eventHandler, options)
{
    GilAcquireGuard guard;
    Py_INCREF(d_mock);
    static const char* const option_names[] = {
            "broker_uri",
            "process_name_override",
            "connect_timeout",
            "disconnect_timeout",
            "open_queue_timeout",
            "configure_queue_timeout",
            "close_queue_timeout",
            "num_processing_threads",
            "blob_buffer_size",
            "channel_high_watermark",
            "event_queue_low_watermark",
            "event_queue_high_watermark",
            "stats_dump_interval"};

    double timeout_connect_secs = time_interval_to_seconds(options.connectTimeout());
    double timeout_disconnect_secs =
            time_interval_to_seconds(options.disconnectTimeout());
    double timeout_open_secs = time_interval_to_seconds(options.openQueueTimeout());
    double timeout_configure_secs =
            time_interval_to_seconds(options.configureQueueTimeout());
    double timeout_close_secs = time_interval_to_seconds(options.closeQueueTimeout());
    double stats_dump_interval_secs =
            time_interval_to_seconds(options.statsDumpInterval());

    bslma::ManagedPtr<PyObject> py_options = RefUtils::toManagedPtr(_Py_DictBuilder(
            option_names,
            "(s# N f f f f f i i i i i f)",
            options.brokerUri().c_str(),
            options.brokerUri().length(),
            PyBytes_FromStringAndSize(
                    options.processNameOverride().c_str(),
                    options.processNameOverride().length()),
            timeout_connect_secs,
            timeout_disconnect_secs,
            timeout_open_secs,
            timeout_configure_secs,
            timeout_close_secs,
            options.numProcessingThreads(),
            options.blobBufferSize(),
            options.channelHighWatermark(),
            options.eventQueueLowWatermark(),
            options.eventQueueHighWatermark(),
            stats_dump_interval_secs));
    if (!py_options) throw bsl::runtime_error("propagating Python error");
    PyObject_SetAttrString(d_mock, "options", py_options.get());
}

MockSession::~MockSession()
{
    GilAcquireGuard guard;
    Py_DECREF(d_mock);
}

int
MockSession::start(const bsls::TimeInterval& timeout)
{
    BMQA_EXPECT_CALL(d_mock_session, start(timeout));
    d_mock_session.start(timeout);
    GilAcquireGuard guard;
    // Obtain data
    double timeout_secs = timeout.seconds() + timeout.nanoseconds() * 1e-9;

    // Call method
    static const char* const names[] = {"timeout"};
    bslma::ManagedPtr<PyObject> mock_ret = RefUtils::toManagedPtr(
            _PyMock_Call(d_mock, "start", names, "(f)", timeout_secs));

    // Return error code
    if (!mock_ret) throw bsl::runtime_error("propagating Python error");
    int ret = PyLong_AsLong(mock_ret.get());
    if (PyErr_Occurred()) throw bsl::runtime_error("propagating Python error");
    return ret;
}

int
MockSession::startAsync(const bsls::TimeInterval& timeout)
{
    (void)timeout;
    assertNotCalled();
    return -1;
}

void
MockSession::stop()
{
    BMQA_EXPECT_CALL(d_mock_session, stop());
    d_mock_session.stop();
    GilAcquireGuard guard;
    bslma::ManagedPtr<PyObject> mock_ret =
            RefUtils::toManagedPtr(PyObject_CallMethod(d_mock, "stop", NULL));
    if (mock_ret.get() != Py_None) {
        throw bsl::runtime_error("expected stop() to return None");
    }
}

void
MockSession::stopAsync()
{
    assertNotCalled();
}

void
MockSession::finalizeStop()
{
    assertNotCalled();
}

void
MockSession::loadMessageEventBuilder(bmqa::MessageEventBuilder* builder)
{
    d_mock_session.loadMessageEventBuilder(builder);
}

void
MockSession::loadConfirmEventBuilder(bmqa::ConfirmEventBuilder* builder)
{
    (void)builder;
    assertNotCalled();
}

void
MockSession::loadMessageProperties(bmqa::MessageProperties* buffer)
{
    d_mock_session.loadMessageProperties(buffer);
}

int
MockSession::getQueueId(bmqa::QueueId* queueId, const bmqt::Uri& uri)
{
    int rc = d_mock_session.getQueueId(queueId, uri);
    bool close_on_get = false;
    {
        GilAcquireGuard guard;
        if (PyObject_HasAttrString(d_mock, "close_on_get")) {
            close_on_get = true;
        }
    }
    if (close_on_get) {
        BMQA_EXPECT_CALL(d_mock_session, closeQueueSync(queueId));
        d_mock_session.closeQueueSync(queueId);
    }
    return rc;
}

int
MockSession::getQueueId(
        bmqa::QueueId* queueId,
        const bmqt::CorrelationId& correlationId)
{
    (void)queueId;
    (void)correlationId;
    assertNotCalled();
    return -1;
}

int
MockSession::openQueue(
        bmqa::QueueId* queueId,
        const bmqt::Uri& uri,
        bsls::Types::Uint64 flags,
        const bmqt::QueueOptions& options,
        const bsls::TimeInterval& timeout)
{
    (void)queueId;
    (void)uri;
    (void)flags;
    (void)options;
    (void)timeout;
    assertNotCalled();
    return -1;
}

int
MockSession::openQueueAsync(
        bmqa::QueueId* queueId,
        const bmqt::Uri& uri,
        bsls::Types::Uint64 flags,
        const bmqt::QueueOptions& options,
        const bsls::TimeInterval& timeout)
{
    (void)queueId;
    (void)uri;
    (void)flags;
    (void)options;
    (void)timeout;
    assertNotCalled();
    return -1;
}

void
MockSession::openQueueAsync(
        bmqa::QueueId* queueId,
        const bmqt::Uri& uri,
        bsls::Types::Uint64 flags,
        const OpenQueueCallback& callback,
        const bmqt::QueueOptions& options,
        const bsls::TimeInterval& timeout)
{
    (void)queueId;
    (void)uri;
    (void)flags;
    (void)callback;
    (void)options;
    (void)timeout;
    assertNotCalled();
}

bmqa::OpenQueueStatus
MockSession::openQueueSync(
        bmqa::QueueId* queueId,
        const bmqt::Uri& uri,
        bsls::Types::Uint64 flags,
        const bmqt::QueueOptions& options,
        const bsls::TimeInterval& timeout)
{
    BMQA_EXPECT_CALL(
            d_mock_session,
            openQueueSync(queueId, uri, flags, options, timeout));
    d_mock_session.openQueueSync(queueId, uri, flags, options, timeout);

    GilAcquireGuard guard;

    // Obtain data
    const bsl::string text_uri = uri.asString();
    static const char* const option_names[] = {
            "max_unconfirmed_messages",
            "max_unconfirmed_bytes",
            "consumer_priority",
            "suspends_on_bad_host_health",
    };
    double double_timeout = timeout.seconds() + timeout.nanoseconds() * 1e-9;

    // Call method
    static const char* const names[] = {"uri", "flags", "options", "timeout"};
    bslma::ManagedPtr<PyObject> mock_ret = RefUtils::toManagedPtr(_PyMock_Call(
            d_mock,
            "openQueueSync",
            names,
            "(N i N f)",
            PyBytes_FromStringAndSize(text_uri.c_str(), text_uri.length()),
            flags,
            _Py_DictBuilder(
                    option_names,
                    "(i i i O)",
                    options.maxUnconfirmedMessages(),
                    options.maxUnconfirmedBytes(),
                    options.consumerPriority(),
                    options.suspendsOnBadHostHealth() ? Py_True : Py_False),
            double_timeout));

    // Return error code
    if (!mock_ret) throw bsl::runtime_error("propagating Python error");
    int ret = PyLong_AsLong(mock_ret.get());
    if (PyErr_Occurred()) throw bsl::runtime_error("propagating Python error");
    bmqt::OpenQueueResult::Enum result = static_cast<bmqt::OpenQueueResult::Enum>(ret);

    maybe_emit_messages(d_mock, &d_mock_session);

    return bmqa::OpenQueueStatus(*queueId, result, "the_error_string");
}

int
MockSession::configureQueue(
        bmqa::QueueId* queueId,
        const bmqt::QueueOptions& options,
        const bsls::TimeInterval& timeout)
{
    (void)queueId;
    (void)options;
    (void)timeout;
    assertNotCalled();
    return -1;
}

int
MockSession::configureQueueAsync(
        bmqa::QueueId* queueId,
        const bmqt::QueueOptions& options,
        const bsls::TimeInterval& timeout)
{
    (void)queueId;
    (void)options;
    (void)timeout;
    assertNotCalled();
    return -1;
}

void
MockSession::configureQueueAsync(
        bmqa::QueueId* queueId,
        const bmqt::QueueOptions& options,
        const ConfigureQueueCallback& callback,
        const bsls::TimeInterval& timeout)
{
    (void)queueId;
    (void)options;
    (void)callback;
    (void)timeout;
    assertNotCalled();
}

bmqa::ConfigureQueueStatus
MockSession::configureQueueSync(
        bmqa::QueueId* queueId,
        const bmqt::QueueOptions& options,
        const bsls::TimeInterval& timeout)
{
    BMQA_EXPECT_CALL(d_mock_session, configureQueueSync(queueId, options, timeout));
    d_mock_session.configureQueueSync(queueId, options, timeout);

    GilAcquireGuard guard;

    // Obtain data
    static const char* const option_names[] = {
            "max_unconfirmed_messages",
            "max_unconfirmed_bytes",
            "consumer_priority",
            "suspends_on_bad_host_health",
    };
    double double_timeout = timeout.seconds() + timeout.nanoseconds() * 1e-9;

    // Call method
    static const char* const names[] = {"options", "timeout"};
    bslma::ManagedPtr<PyObject> mock_ret = RefUtils::toManagedPtr(_PyMock_Call(
            d_mock,
            "configureQueueSync",
            names,
            "(N f)",
            _Py_DictBuilder(
                    option_names,
                    "(i i i O)",
                    options.maxUnconfirmedMessages(),
                    options.maxUnconfirmedBytes(),
                    options.consumerPriority(),
                    options.suspendsOnBadHostHealth() ? Py_True : Py_False),
            double_timeout));

    // Return error code
    if (!mock_ret) throw bsl::runtime_error("propagating Python error");
    int ret = PyLong_AsLong(mock_ret.get());
    if (PyErr_Occurred()) throw bsl::runtime_error("propagating Python error");
    bmqt::ConfigureQueueResult::Enum result =
            static_cast<bmqt::ConfigureQueueResult::Enum>(ret);

    return bmqa::ConfigureQueueStatus(*queueId, result, "the_error_string");
}

int
MockSession::closeQueue(bmqa::QueueId* queueId, const bsls::TimeInterval& timeout)
{
    (void)queueId;
    (void)timeout;
    assertNotCalled();
    return -1;
}

int
MockSession::closeQueueAsync(bmqa::QueueId* queueId, const bsls::TimeInterval& timeout)
{
    (void)queueId;
    (void)timeout;
    assertNotCalled();
    return -1;
}

void
MockSession::closeQueueAsync(
        bmqa::QueueId* queueId,
        const CloseQueueCallback& callback,
        const bsls::TimeInterval& timeout)
{
    (void)queueId;
    (void)callback;
    (void)timeout;
    assertNotCalled();
}

bmqa::CloseQueueStatus
MockSession::closeQueueSync(bmqa::QueueId* queueId, const bsls::TimeInterval& timeout)
{
    BMQA_EXPECT_CALL(d_mock_session, closeQueueSync(queueId, timeout));
    d_mock_session.closeQueueSync(queueId, timeout);
    GilAcquireGuard guard;

    // Obtain data
    double double_timeout = timeout.seconds() + timeout.nanoseconds() * 1e-9;

    // Call method
    static const char* const names[] = {"timeout"};
    bslma::ManagedPtr<PyObject> mock_ret = RefUtils::toManagedPtr(
            _PyMock_Call(d_mock, "closeQueueSync", names, "(f)", double_timeout));

    // Return error code
    if (!mock_ret) throw bsl::runtime_error("propagating Python error");
    int ret = PyLong_AsLong(mock_ret.get());
    if (PyErr_Occurred()) throw bsl::runtime_error("propagating Python error");
    bmqt::CloseQueueResult::Enum result =
            static_cast<bmqt::CloseQueueResult::Enum>(ret);
    return bmqa::CloseQueueStatus(*queueId, result, "the_error_string");
}

bmqa::Event
MockSession::nextEvent(const bsls::TimeInterval& timeout)
{
    (void)timeout;
    assertNotCalled();
    return bmqa::Event();
}

int
MockSession::post(const bmqa::MessageEvent& event)
{
    BMQA_EXPECT_CALL(d_mock_session, post(event));
    d_mock_session.post(event);

    // Ensure that no events are accumulated in the MockSession.
    bmqa::MessageEvent _message_event;
    d_mock_session.popPostedEvent(&_message_event);

    GilAcquireGuard guard;

    bmqa::MessageIterator message_iterator = event.messageIterator();
    message_iterator.nextMessage();
    const bmqa::Message& message = message_iterator.message();

    // Call method
    static const char* const names[] =
            {"payload", "queue_uri", "properties", "compression_algorithm_type"};
    bsl::vector<bsl::string> ignored_collated_errors;
    bslma::ManagedPtr<PyObject> mock_ret = RefUtils::toManagedPtr(_PyMock_Call(
            d_mock,
            "post",
            names,
            "(N N N i)",
            MessageUtils::get_message_data(message),
            MessageUtils::get_message_queue_uri(message),
            MessageUtils::get_message_properties(&ignored_collated_errors, message),
            message.compressionAlgorithmType()));

    // Return error code
    if (!mock_ret) throw bsl::runtime_error("propagating Python error");
    int ret = PyLong_AsLong(mock_ret.get());
    if (PyErr_Occurred()) throw bsl::runtime_error("propagating Python error");

    maybe_emit_acks(d_mock, &d_mock_session);

    return ret;
}

int
MockSession::confirmMessage(const bmqa::Message& message)
{
    (void)message;
    assertNotCalled();
    return -1;
}

int
MockSession::confirmMessage(const bmqa::MessageConfirmationCookie& cookie)
{
    BMQA_EXPECT_CALL(d_mock_session, confirmMessage(cookie));
    d_mock_session.confirmMessage(cookie);
    GilAcquireGuard guard;

    const bsl::string& c_queue_uri = cookie.queueId().uri().asString();
    PyObject* py_queue_uri =
            PyBytes_FromStringAndSize(c_queue_uri.c_str(), c_queue_uri.length());

    const bmqt::MessageGUID& c_guid = cookie.messageGUID();
    PyObject* py_guid =
            PyBytes_FromStringAndSize(NULL, bmqt::MessageGUID::e_SIZE_BINARY);
    c_guid.toBinary(reinterpret_cast<unsigned char*>(PyBytes_AsString(py_guid)));

    // Call method
    static const char* const names[] = {"queue_uri", "guid"};
    bslma::ManagedPtr<PyObject> mock_ret = RefUtils::toManagedPtr(_PyMock_Call(
            d_mock,
            "confirmMessage",
            names,
            "(N N)",
            py_queue_uri,
            py_guid));

    // Return error code
    if (!mock_ret) {
        throw bsl::runtime_error("propagating Python error");
    }
    int ret = PyLong_AsLong(mock_ret.get());
    if (PyErr_Occurred()) {
        throw bsl::runtime_error("propagating Python error");
    }
    return ret;
}

int
MockSession::confirmMessages(bmqa::ConfirmEventBuilder* builder)
{
    (void)builder;
    assertNotCalled();
    return -1;
}

int
MockSession::configureMessageDumping(const bslstl::StringRef& command)
{
    (void)command;
    assertNotCalled();
    return -1;
}

}  // namespace pybmq
}  // namespace BloombergLP
