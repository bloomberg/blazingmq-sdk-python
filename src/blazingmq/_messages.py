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

from typing import Optional
from typing import TYPE_CHECKING

from ._enums import AckStatus
from ._typing import PropertyTypeDict
from ._typing import PropertyValueDict
from .exceptions import Error

if TYPE_CHECKING:
    # Safely perform circular references only during static type analysis
    from . import _ext  # pragma: no cover


def pretty_hex(blob: bytes) -> str:
    return blob.hex().upper()


def create_message(
    data: bytes,
    guid: bytes,
    queue_uri: str,
    properties: PropertyValueDict,
    property_types: PropertyTypeDict,
) -> Message:
    inst = Message.__new__(Message)
    assert isinstance(inst, Message)
    inst._set_attrs(data, guid, queue_uri, properties, property_types)
    return inst


class Message:
    """A class representing a message received from BlazingMQ.

    A `Message` represents a message delivered by BlazingMQ from a producer
    to this queue. This message can only be received if the queue is
    opened with 'read=True' mode enabled.

    Attributes:
        data (bytes): Payload for the message received from BlazingMQ.
        guid (bytes): Globally unique id for this message.
        queue_uri (str): Queue URI this message is for.
        properties (dict): A dictionary of BlazingMQ message properties.
            The dictionary keys must be :class:`str` representing the property
            names and the values must be of type :class:`str`, :class:`bytes`,
            :class:`bool` or :class:`int`.
        property_types (dict): A mapping of property names to
            `PropertyType` types. The dictionary is guaranteed to provide
            a value for each key already present in `Message.properties`
    """

    def _set_attrs(
        self,
        data: bytes,
        guid: bytes,
        queue_uri: str,
        properties: PropertyValueDict,
        property_types: PropertyTypeDict,
    ) -> None:
        """Teach mypy what our instance variables are despite our private __init__"""
        self.data = data
        self.guid = guid
        self.queue_uri = queue_uri
        self.properties = properties
        self.property_types = property_types

    def __init__(self) -> None:
        raise Error("The Message class does not have a public constructor.")

    def __repr__(self) -> str:
        return f"<Message[{pretty_hex(self.guid)}] for {self.queue_uri}>"


def create_message_handle(message: Message, ext_session: _ext.Session) -> MessageHandle:
    inst = MessageHandle.__new__(MessageHandle)
    assert isinstance(inst, MessageHandle)
    inst._set_attrs(message, ext_session)
    return inst


class MessageHandle:
    """Operations that can be performed on a `Message`.

    An instance of this class is received in the ``on_message``
    callback along with an instance of a `Message`.
    """

    def confirm(self) -> None:
        """Confirm the message received along with this handle.

        See `Session.confirm` for more details.

        Raises:
            `~blazingmq.Error`: If the confirm message request
                was not successful.
        """
        self._ext_session.confirm(self._message)

    def _set_attrs(self, message: Message, ext_session: _ext.Session) -> None:
        """Teach mypy what our instance variables are despite our private __init__"""
        self._message = message
        self._ext_session = ext_session

    def __init__(self) -> None:
        raise Error("The MessageHandle class does not have a public constructor.")

    def __repr__(self) -> str:
        return "<MessageHandle[{}] for {}>".format(
            pretty_hex(self._message.guid),
            self._message.queue_uri,
        )


def create_ack(
    guid: Optional[bytes], status: AckStatus, status_description: str, queue_uri: str
) -> Ack:
    inst = Ack.__new__(Ack)
    assert isinstance(inst, Ack)
    inst._set_attrs(guid, status, status_description, queue_uri)
    return inst


class Ack:
    """Acknowledgment message

    An `Ack` is a notification from BlazingMQ to the application,
    specifying that the message has been received. This is valuable
    for ensuring delivery of messages.

    These messages will be received in the optionally provided callback to
    `Session.post()`.

    An `Ack` is by itself not an indication of success unless it has a status of
    `AckStatus.SUCCESS`.

    Attributes:
        guid (bytes): a globally unique identifier generated by BlazingMQ for the
            message that was successfully posted. This can be correlated between the
            producer and consumer to verify the flow of messages.
        queue_uri (str): the queue that this message was routed to. This is useful
            if you have many queues and you want to route this particular `Ack` to a
            particular queue.
        status (AckStatus): the `AckStatus` indicating the result of the post
            operation. Unless this is of type `AckStatus.SUCCESS`, the post has
            failed and potentially needs to be dealt with.
    """

    def _set_attrs(
        self,
        guid: Optional[bytes],
        status: AckStatus,
        status_description: str,
        queue_uri: str,
    ) -> None:
        """Teach mypy what our instance variables are despite our private __init__"""
        self.guid = guid
        self.status = status
        self._status_description = status_description
        self.queue_uri = queue_uri

    def __init__(self) -> None:
        raise Error("The Ack class does not have a public constructor.")

    def __repr__(self) -> str:
        guid_identifier = "" if self.guid is None else f"[{pretty_hex(self.guid)}]"
        return "<Ack{} {} for {}>".format(
            guid_identifier,
            self._status_description,
            self.queue_uri,
        )
