# Copyright 2019-2023 Bloomberg Finance L.P.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import os
import sys
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import Mapping
from typing import Optional
from typing import TYPE_CHECKING
from typing import Tuple
from typing import Type
from typing import Union
import weakref

from ._enums import AckStatus
from ._enums import PropertyType
from ._messages import Ack
from ._messages import Message
from ._messages import MessageHandle
from ._messages import create_ack
from ._messages import create_message
from ._messages import create_message_handle
from .session_events import InterfaceError
from .session_events import QueueEvent
from .session_events import QueueReopenFailed
from .session_events import QueueReopened
from .session_events import QueueResumeFailed
from .session_events import QueueResumed
from .session_events import QueueSuspendFailed
from .session_events import QueueSuspended
from .session_events import SessionEvent

if TYPE_CHECKING:
    # Safely perform circular references only during static type analysis
    from . import _ext  # pragma: no cover


def on_session_event(
    user_callback: Callable[[SessionEvent], None],
    event_type_mapping: Dict[int, Type[SessionEvent]],
    error_description: bytes,
    sdk_event: Optional[Tuple[int, bytes, int, bytes, str]] = None,
) -> None:
    if sdk_event is None:
        # This is a synthetically generated InterfaceError being produced in
        # response to input from the SDK that we can't handle.
        return user_callback(InterfaceError(error_description.decode()))

    # Otherwise, we're passing a bmqa::SessionEvent we've received to our user
    event_type, event_name, status_code, status_name, queue_uri = sdk_event
    event_cls = event_type_mapping.get(event_type, InterfaceError)

    # Prepare event message
    if event_cls is InterfaceError:
        msg = "Unexpected event type: %s" % event_name.decode()
    elif status_code != 0:
        msg = "%s%s%s (%d)" % (
            error_description.decode(),
            ": " if error_description else "",
            status_name.decode(),
            status_code,
        )
    else:
        msg = None

    # Create event
    if issubclass(event_cls, QueueEvent):
        failure_class_by_success_class = {
            QueueReopened: QueueReopenFailed,
            QueueResumed: QueueResumeFailed,
            QueueSuspended: QueueSuspendFailed,
        }

        if status_code != 0:
            event_cls = failure_class_by_success_class[event_cls]

        assert queue_uri
        event: SessionEvent = event_cls(queue_uri, msg)
    else:
        event = event_cls(msg)

    # Invoke user callback
    user_callback(event)


PropertiesAndTypesDictsType = Tuple[Dict[str, Union[int, bytes]], Dict[str, int]]


def on_message(
    user_callback: Callable[[Message, MessageHandle], None],
    ext_session_wr: weakref.ref[_ext.Session],
    property_type_to_py: Mapping[int, PropertyType],
    messages: Iterable[Tuple[bytes, bytes, bytes, PropertiesAndTypesDictsType]],
) -> None:
    ext_session = ext_session_wr()
    assert ext_session is not None, "ext.Session has been deleted"
    for data, guid, queue_uri, properties_tuple in messages:
        properties, property_types = properties_tuple
        property_types_py = {
            k: property_type_to_py[v] for k, v in property_types.items()
        }
        message = create_message(
            data, guid, queue_uri.decode(), properties, property_types_py
        )
        message_handle = create_message_handle(message, ext_session)
        user_callback(message, message_handle)

    del message_handle  # The message handle holds a reference to the extension session.
    if sys.getrefcount(ext_session) == 2:  # covered in a subprocess  # pragma: no cover
        # Dropping our reference to the extension session will drop its reference count
        # to 0, calling __dealloc__ and stop() from its own background thread.
        print(
            "Deadlock detected by blazingmq after calling %s; aborting process."
            % user_callback,
            file=sys.stderr,
        )
        try:
            import faulthandler

            faulthandler.dump_traceback()
        finally:
            # `faulthandler` only exists on 3; abort even if it doesn't exist or fails.
            sys.stderr.flush()
            os.abort()


def on_ack(
    ack_status_mapping: Dict[int, AckStatus],
    acks: Iterable[Tuple[int, bytes, Optional[bytes], bytes, Callable[[Ack], None]]],
) -> None:
    for status, status_description, guid, queue_uri, user_callback in acks:
        py_status = ack_status_mapping.get(status, AckStatus.UNRECOGNIZED)
        user_callback(
            create_ack(
                guid,
                py_status,
                status_description.decode(),
                queue_uri.decode(),
            )
        )


def on_message_create_interface_error(
    user_on_session_event: Callable[[SessionEvent], None],
    _: Any,
) -> None:
    error_description = "Messages received but no callback configured"
    user_on_session_event(InterfaceError(error_description))
