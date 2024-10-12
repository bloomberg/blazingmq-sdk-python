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

#include <pybmq_messageutils.h>
#include <pybmq_refutils.h>

#include <bdlbb_blob.h>
#include <bdlbb_blobutil.h>
#include <bsl_sstream.h>
#include <bslmf_assert.h>

#include <bmqt_messageguid.h>
#include <bmqt_propertytype.h>
#include <bmqt_resultcode.h>

namespace BloombergLP {
namespace pybmq {

namespace {

// Support needs to be added in this file for any new property type added to
// the C++ BlazingMQ SDK.  Since we can't write automated tests for
// unrecognized property types, any code attempting to handle them cannot be
// adequately tested and will be subject to bit rot.  By default we prevent
// building against a version of the SDK that can deliver property types that
// we don't recognize.  If users must build an old version of blazingmq against
// a new libbmq, we provide a macro they can set to disable this check.
#ifndef PYBMQ_DISABLE_PROPERTY_TYPE_EXHAUSTIVENESS_CHECK
// clang-format off
// Disable clang-format: it wants to wrap these lines, but since BSLMF_ASSERT
// violations result in compilation failures and the compiler only shows the
// line that the error occurred on, not wrapped lines below it, this would
// negatively impact users' ability to debug this assertion failing.
BSLMF_ASSERT(bmqt::PropertyType::k_LOWEST_SUPPORTED_PROPERTY_TYPE == bmqt::PropertyType::e_BOOL);
BSLMF_ASSERT(bmqt::PropertyType::k_HIGHEST_SUPPORTED_PROPERTY_TYPE == bmqt::PropertyType::e_BINARY);
// clang-format on
#endif

bool
intOrLongCheck(PyObject* o)
{
#if PY_MAJOR_VERSION >= 3
    return PyLong_Check(o);
#else
    return PyInt_Check(o) || PyLong_Check(o);
#endif
}

template<typename T>
T
toIntegralWithRangeCheck(PyObject* obj, const bsl::string& key)
{
    int overflow;
    long long min = bsl::numeric_limits<T>::min();
    long long max = bsl::numeric_limits<T>::max();
    long long val = PyLong_AsLongLongAndOverflow(obj, &overflow);
    if (val == -1 && PyErr_Occurred()) {
        return -1;
    }
    if (overflow || val < min || val > max) {
        bsl::ostringstream oss;
        oss << "Property " << key << " value must be between [" << min << ", " << max
            << "], inclusive";
        PyErr_SetString(PyExc_ValueError, oss.str().c_str());
        return -1;
    }
    return val;
}

}  // namespace

PyObject*
MessageUtils::get_acks(const bmqa::MessageEvent& event)
{
    bslma::ManagedPtr<PyObject> acks = RefUtils::toManagedPtr(PyList_New(0));
    if (!acks) return NULL;

    bmqa::MessageIterator message_iterator = event.messageIterator();
    while (message_iterator.nextMessage()) {
        const bmqa::Message& message = message_iterator.message();

        PyObject* guid;
        int status = message.ackStatus();
        if (!status) {
            guid = MessageUtils::get_message_guid(message);
        } else {
            guid = RefUtils::ref(Py_None);
        }

        // The BlazingMQ SDK can send a negative acknowledgment for a message
        // even when no correlation id was provided. If it does, ignore it.
        // The SDK already has a (throttled) log for NACKs, which is enough to
        // tell our user that something went wrong.
        if (message.correlationId().isUnset()) {
            BSLS_ASSERT(0 != status);
            continue;
        }

        PyObject* callback = (PyObject*)message.correlationId().thePointer();

        bslma::ManagedPtr<PyObject> pymessage = RefUtils::toManagedPtr(Py_BuildValue(
                "(i N N N N)",
                status,
                PyBytes_FromString(
                        bmqt::AckResult::toAscii((bmqt::AckResult::Enum)status)),
                guid,
                MessageUtils::get_message_queue_uri(message),
                callback));
        if (!pymessage) {
            return NULL;
        }

        if (0 != PyList_Append(acks.get(), pymessage.get())) {
            return NULL;
        }
    }
    return acks.release().first;
}

PyObject*
MessageUtils::get_message_data(const bmqa::Message& message)
{
    bdlbb::Blob blob;
    message.getData(&blob);
    PyObject* payload = PyBytes_FromStringAndSize(NULL, blob.length());
    if (!payload) {
        return NULL;
    }
    bdlbb::BlobUtil::copy(PyBytes_AsString(payload), blob, 0, blob.length());
    return payload;
}

PyObject*
MessageUtils::get_message_guid(const bmqa::Message& message)
{
    PyObject* guid = PyBytes_FromStringAndSize(NULL, bmqt::MessageGUID::e_SIZE_BINARY);
    if (!guid) {
        return NULL;
    }
    message.messageGUID().toBinary(
            reinterpret_cast<unsigned char*>(PyBytes_AsString(guid)));
    return guid;
}

bool
MessageUtils::get_message_property_and_type(
        PyObject* properties,
        PyObject* property_types,
        bsl::vector<bsl::string>* collated_errors,
        const bmqa::MessagePropertiesIterator& iterator)
{
    bmqt::PropertyType::Enum ptype = iterator.type();
    bslma::ManagedPtr<PyObject> value;
    switch (ptype) {
        case bmqt::PropertyType::e_BOOL: {
            value = RefUtils::toManagedPtr(PyBool_FromLong(iterator.getAsBool()));
        } break;

        case bmqt::PropertyType::e_CHAR: {
            const char the_char = iterator.getAsChar();
            value = RefUtils::toManagedPtr(PyBytes_FromStringAndSize(&the_char, 1));
        } break;

        case bmqt::PropertyType::e_STRING: {
            const bsl::string& the_string = iterator.getAsString();
            value = RefUtils::toManagedPtr(PyUnicode_FromStringAndSize(
                    the_string.c_str(),
                    the_string.length()));
            if (!value && PyErr_ExceptionMatches(PyExc_UnicodeDecodeError)) {
                PyErr_Clear();
                collated_errors->push_back(
                        "STRING property '" + iterator.name() + "' has non-UTF-8 data");
                return true;  // Skip this property; we've enqueued an InterfaceError
            }
        } break;

        case bmqt::PropertyType::e_BINARY: {
            const bsl::vector<char>& the_data = iterator.getAsBinary();
            value = RefUtils::toManagedPtr(
                    PyBytes_FromStringAndSize(the_data.data(), the_data.size()));
        } break;

        case bmqt::PropertyType::e_SHORT: {
            value = RefUtils::toManagedPtr(PyLong_FromLongLong(iterator.getAsShort()));
        } break;

        case bmqt::PropertyType::e_INT32: {
            value = RefUtils::toManagedPtr(PyLong_FromLongLong(iterator.getAsInt32()));
        } break;

        case bmqt::PropertyType::e_INT64: {
            value = RefUtils::toManagedPtr(PyLong_FromLongLong(iterator.getAsInt64()));
        } break;

        case bmqt::PropertyType::e_UNDEFINED:
        default: {
            bsl::ostringstream oss;
            oss << "'" << iterator.name() << "' property type is unrecognized, type "
                << ptype << " received.";
            collated_errors->push_back(oss.str());
            return true;  // Skip this property; we've enqueued an InterfaceError
        }
    }

    if (!value) {
        return false;
    }

    if (PyDict_SetItemString(properties, iterator.name().c_str(), value.get())) {
        return false;
    }

    if (PyDict_SetItemString(
                property_types,
                iterator.name().c_str(),
                PyLong_FromLong(ptype)))
    {
        return false;
    }

    return true;
}

PyObject*
MessageUtils::get_message_properties(
        bsl::vector<bsl::string>* collated_errors,
        const bmqa::Message& message)
{
    bslma::ManagedPtr<PyObject> py_properties = RefUtils::toManagedPtr(PyDict_New());
    bslma::ManagedPtr<PyObject> py_property_types =
            RefUtils::toManagedPtr(PyDict_New());
    if (!py_properties || !py_property_types) {
        return NULL;
    }

    if (!message.hasProperties()) {
        return Py_BuildValue(
                "(N N)",
                py_properties.release().first,
                py_property_types.release().first);
    }

    bmqa::MessageProperties properties;
    int rc = message.loadProperties(&properties);
    if (rc != 0) {
        PyErr_SetString(
                PyExc_RuntimeError,
                "Failed to load properties from an incoming message.");
        return NULL;
    }
    bmqa::MessagePropertiesIterator propIter(&properties);
    while (propIter.hasNext()) {
        if (!get_message_property_and_type(
                    py_properties.get(),
                    py_property_types.get(),
                    collated_errors,
                    propIter))
        {
            return NULL;
        }
    }
    return Py_BuildValue(
            "(N N)",
            py_properties.release().first,
            py_property_types.release().first);
}

PyObject*
MessageUtils::get_message_queue_uri(const bmqa::Message& message)
{
    const bsl::string& uri = message.queueId().uri().asString();
    return PyBytes_FromStringAndSize(uri.c_str(), uri.length());
}

PyObject*
MessageUtils::get_messages(
        const bmqa::MessageEvent& event,
        PyObject* session_event_callback)
{
    bslma::ManagedPtr<PyObject> messages = RefUtils::toManagedPtr(PyList_New(0));
    if (!messages) {
        return NULL;
    }

    bmqa::MessageIterator message_iterator = event.messageIterator();
    while (message_iterator.nextMessage()) {
        const bmqa::Message& message = message_iterator.message();
        bsl::vector<bsl::string> collated_errors;
        bslma::ManagedPtr<PyObject> pymessage = RefUtils::toManagedPtr(Py_BuildValue(
                "(N N N N)",
                MessageUtils::get_message_data(message),
                MessageUtils::get_message_guid(message),
                MessageUtils::get_message_queue_uri(message),
                MessageUtils::get_message_properties(&collated_errors, message)));

        if (!pymessage) {
            return NULL;
        }
        if (0 != PyList_Append(messages.get(), pymessage.get())) {
            return NULL;
        }
        if (!collated_errors.empty()) {
            bsl::ostringstream oss;
            for (size_t i = 0; i < collated_errors.size(); ++i) {
                oss << collated_errors[i] << "\n";
            }
            bslma::ManagedPtr<PyObject> rv =
                    RefUtils::toManagedPtr(PyObject_CallFunction(
                            session_event_callback,
                            "(N)",
                            PyBytes_FromString(oss.str().c_str())));
            if (!rv) {
                PyErr_Print();
            }
        }
    }
    return messages.release().first;
}

bool
MessageUtils::load_message_properties(
        bmqa::MessageProperties* c_properties,
        PyObject* py_properties)
{
    if (!PyDict_Check(py_properties)) {
        PyErr_SetString(PyExc_ValueError, "'properties' is not a dictionary.");
        return false;
    }

    PyObject* py_key;
    PyObject* py_value_tuple;
    Py_ssize_t pos = 0;

    while (PyDict_Next(py_properties, &pos, &py_key, &py_value_tuple)) {
        if (!PyBytes_Check(py_key)) {
            PyErr_SetString(PyExc_ValueError, "expected bytes type for key");
            return false;
        }
        const char* c_ptr_key = PyBytes_AsString(py_key);
        if (!c_ptr_key) {
            return false;
        }

        const bsl::string c_key(c_ptr_key, PyBytes_Size(py_key));
        if (!PyTuple_Check(py_value_tuple)) {
            bsl::ostringstream oss;
            oss << "'" << c_key << "' value is not a tuple.";
            PyErr_SetString(PyExc_TypeError, oss.str().c_str());
            return false;
        }

        PyObject* py_value = PyTuple_GetItem(py_value_tuple, 0);
        PyObject* py_type_code = PyTuple_GetItem(py_value_tuple, 1);
        if (!py_value || !py_type_code) {
            return false;
        }
        long long property_type = PyLong_AsLongLong(py_type_code);
        if (PyErr_Occurred()) {
            return false;
        }

#define PY_TYPE_CHECK(PY_TYPE_FUNC, EXPECTED_TYPE, OBJECT, OBJECT_KEY)                 \
    do {                                                                               \
        if (!PY_TYPE_FUNC(OBJECT)) {                                                   \
            bsl::ostringstream oss;                                                    \
            oss << "'" << OBJECT_KEY << "' value is of the incorrect type, " << "'"    \
                << Py_TYPE(OBJECT)->tp_name << "' provided, '" << EXPECTED_TYPE        \
                << "' expected.";                                                      \
            PyErr_SetString(PyExc_TypeError, oss.str().c_str());                       \
            return false;                                                              \
        }                                                                              \
    } while (0)

        int set_rc = 0;
        switch (property_type) {
            case bmqt::PropertyType::e_CHAR: {
                PY_TYPE_CHECK(PyBytes_Check, "bytes", py_value, c_key);
                Py_ssize_t size = PyBytes_Size(py_value);
                if (size != 1) {
                    bsl::ostringstream oss;
                    oss << "'" << c_key << "' value does not have exactly 1 byte, "
                        << size << " bytes provided.";
                    PyErr_SetString(PyExc_TypeError, oss.str().c_str());
                    return false;
                }
                const char c_value = PyBytes_AsString(py_value)[0];
                set_rc = c_properties->setPropertyAsChar(c_key, c_value);
            } break;

            case bmqt::PropertyType::e_STRING: {
                PY_TYPE_CHECK(PyBytes_Check, "bytes", py_value, c_key);
                const char* c_value = PyBytes_AsString(py_value);
                Py_ssize_t c_value_size = PyBytes_Size(py_value);
                set_rc = c_properties->setPropertyAsString(
                        c_key,
                        bsl::string(c_value, c_value_size));
            } break;

            case bmqt::PropertyType::e_BINARY: {
                PY_TYPE_CHECK(PyBytes_Check, "bytes", py_value, c_key);
                const char* c_value_raw = PyBytes_AsString(py_value);
                Py_ssize_t c_value_size = PyBytes_Size(py_value);
                bsl::vector<char> c_value(c_value_raw, c_value_raw + c_value_size);
                set_rc = c_properties->setPropertyAsBinary(c_key, c_value);
            } break;

            case bmqt::PropertyType::e_BOOL: {
                PY_TYPE_CHECK(PyBool_Check, "bool", py_value, c_key);
                set_rc =
                        c_properties->setPropertyAsBool(c_key, PyLong_AsLong(py_value));
            } break;

            case bmqt::PropertyType::e_SHORT: {
                PY_TYPE_CHECK(intOrLongCheck, "int", py_value, c_key);
                short c_value = toIntegralWithRangeCheck<short>(py_value, c_key);
                if (c_value == -1 && PyErr_Occurred()) {
                    return false;
                }
                set_rc = c_properties->setPropertyAsShort(c_key, c_value);
            } break;

            case bmqt::PropertyType::e_INT32: {
                PY_TYPE_CHECK(intOrLongCheck, "int", py_value, c_key);
                int32_t c_value = toIntegralWithRangeCheck<int32_t>(py_value, c_key);
                if (c_value == -1 && PyErr_Occurred()) {
                    return false;
                }
                set_rc = c_properties->setPropertyAsInt32(c_key, c_value);
            } break;

            case bmqt::PropertyType::e_INT64: {
                PY_TYPE_CHECK(intOrLongCheck, "int", py_value, c_key);
                bsls::Types::Int64 c_value =
                        toIntegralWithRangeCheck<bsls::Types::Int64>(py_value, c_key);
                if (c_value == -1 && PyErr_Occurred()) {
                    return false;
                }
                set_rc = c_properties->setPropertyAsInt64(c_key, c_value);
            } break;

            case bmqt::PropertyType::e_UNDEFINED:
            default: {
                bsl::ostringstream oss;
                oss << "Unsupported property type " << property_type << " ("
                    << (bmqt::PropertyType::Enum)property_type << ")";
                PyErr_SetString(PyExc_ValueError, oss.str().c_str());

                return false;
            }
        }
        if (set_rc) {
            bsl::ostringstream oss;
            oss << "Failed to set key '" << c_key << "' with rc: " << set_rc;
            PyErr_SetString(PyExc_ValueError, oss.str().c_str());
            return false;
        }
    }
#undef PY_TYPE_CHECK

    return true;
}

}  // namespace pybmq
}  // namespace BloombergLP
