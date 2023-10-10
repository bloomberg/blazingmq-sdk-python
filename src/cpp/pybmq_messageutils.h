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

#ifndef INCLUDED_PYBMQ_MESSAGEUTILS
#define INCLUDED_PYBMQ_MESSAGEUTILS

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <bmqa_message.h>
#include <bmqa_messageevent.h>
#include <bmqa_messageproperties.h>

#include <bsl_string.h>
#include <bsl_vector.h>

namespace BloombergLP {
namespace pybmq {

struct MessageUtils
{
    // CLASS METHODS
    static PyObject* get_acks(const bmqa::MessageEvent& event);
    // Convert every acknowledgement in the specified 'event' into a tuple object,
    // returning them in a list.

    static PyObject* get_message_data(const bmqa::Message& message);
    // Get the payload of a BlazingMQ message and convert it into a tuple
    // object to be processed in Python.

    static PyObject* get_message_guid(const bmqa::Message& message);
    // Get the BlazingMQ message GUID as Python bytes object.

    static bool get_message_property_and_type(
            PyObject* properties,
            PyObject* property_types,
            bsl::vector<bsl::string>* collated_errors,
            const bmqa::MessagePropertiesIterator& iterator);
    // Load the property and type associated with the specified iterator into the
    // specified 'properties' and 'property_types' Python dictionaries.

    static PyObject* get_message_properties(
            bsl::vector<bsl::string>* collated_errors,
            const bmqa::Message& message);
    // Get the BlazingMQ message properties as Python dictionary object.

    static PyObject* get_message_queue_uri(const bmqa::Message& message);
    // Get the BlazingMQ message Queue URI as bytes object

    static PyObject*
    get_messages(const bmqa::MessageEvent& event, PyObject* session_event_callback);
    // Convert every message in the specified 'event' into a tuple object, returning
    // them in a list.

    static bool load_message_properties(
            bmqa::MessageProperties* c_properties,
            PyObject* py_properties);
    // Convert properties specified in 'py_properties' into a 'bmqa::MessageProperties'
    // and load it into the specified 'properties' parameter.
};

}  // namespace pybmq
}  // namespace BloombergLP

#endif
