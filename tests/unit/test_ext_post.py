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

import weakref

from blazingmq import CompressionAlgorithmType
from blazingmq import exceptions
from blazingmq._ext import COMPRESSION_ALGO_FROM_PY_MAPPING as compression_map
from blazingmq._ext import Session
import pytest

from .support import QUEUE_NAME
from .support import dummy_callback
from .support import sdk_mock


@pytest.mark.parametrize(
    "post_rc, post_error",
    [(-1, "UNKNOWN"), (-3, "NOT_CONNECTED"), (-5, "NOT_SUPPORTED"), (-8, "NOT_READY")],
)
def test_post_fails_with_error(post_rc, post_error):
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, post=post_rc, stop=None)
    session = Session(dummy_callback, _mock=mock)
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )

    # WHEN
    with pytest.raises(Exception) as exc:
        session.post(QUEUE_NAME, b"bladiblah")

    # THEN
    assert exc.type is exceptions.Error
    assert exc.match(f"Failed to post message to .+dummy_queue queue: {post_error}")


def test_post_failure_reference_not_leaked():
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, post=-1, stop=None)
    session = Session(dummy_callback, _mock=mock)
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )

    def go_on(*args):
        pass

    cb_ref = weakref.ref(go_on)

    # WHEN
    with pytest.raises(Exception) as exc:
        session.post(QUEUE_NAME, b"bladiblah", on_ack=go_on)
    del go_on

    # THEN
    assert exc.type is exceptions.Error
    assert not cb_ref()


def test_post_invalid_queue_reference_not_leaked():
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, post=0, stop=None)
    session = Session(dummy_callback, _mock=mock)
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )

    def go_on(*args):
        pass

    cb_ref = weakref.ref(go_on)

    # WHEN
    with pytest.raises(Exception) as exc:
        session.post(QUEUE_NAME + b"1", b"bladiblah", on_ack=go_on)
    del go_on

    # THEN
    assert exc.type is exceptions.Error
    assert not cb_ref()


@pytest.mark.parametrize(
    "prop_type, expected_exception",
    [(100, ValueError), (2**63, OverflowError), ("", TypeError)],
)
def test_post_with_invalid_property_type(prop_type, expected_exception):
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, post=0, stop=None)
    session = Session(dummy_callback, _mock=mock)
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )
    payload = b"Some_message"

    # WHEN
    with pytest.raises(Exception) as exc:
        session.post(QUEUE_NAME, payload, {b"test": (b"", prop_type)})

    # THEN
    assert exc.type is expected_exception


def test_post_with_empty_key():
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, post=0, stop=None)
    session = Session(dummy_callback, _mock=mock)
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )
    payload = b"Some_message"

    # WHEN
    with pytest.raises(Exception) as exc:
        session.post(QUEUE_NAME, payload, {b"": (b"something", 7)})

    # THEN
    assert exc.type is ValueError
    assert exc.match("Failed to set key '' with rc: -?[0-9]+")


@pytest.mark.parametrize("values", [(b"something",), (1,), tuple()])
def test_post_with_insufficient_tuple_values(values):
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, post=0, stop=None)
    session = Session(dummy_callback, _mock=mock)
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )
    payload = b"Some_message"

    # WHEN
    with pytest.raises(Exception) as exc:
        session.post(QUEUE_NAME, payload, {b"": values})

    # THEN
    assert exc.type is IndexError


def test_post_with_non_tuple_value():
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, post=0, stop=None)
    session = Session(dummy_callback, _mock=mock)
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )
    payload = b"Some_message"

    # WHEN
    with pytest.raises(Exception) as exc:
        session.post(QUEUE_NAME, payload, {b"the_key": []})

    # THEN
    assert exc.type is TypeError
    assert exc.match("'the_key' value is not a tuple.")


def test_post_unicode_key():
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, post=0, stop=None)
    session = Session(dummy_callback, _mock=mock)
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )
    payload = b"Some_message"

    # WHEN
    with pytest.raises(Exception) as exc:
        session.post(QUEUE_NAME, payload, {"hello": (b"something", 7)})

    # THEN
    assert exc.type is ValueError
    assert exc.match("expected bytes type for key")


@pytest.mark.parametrize(
    "compression",
    [CompressionAlgorithmType.NONE, CompressionAlgorithmType.ZLIB],
)
def test_session_with_valid_compression(compression):
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, post=0, stop=None)
    session = Session(
        dummy_callback,
        message_compression_algorithm=compression,
        _mock=mock,
    )
    session.open_queue_sync(
        QUEUE_NAME,
        read=True,
        write=True,
        consumer_priority=0,
        max_unconfirmed_messages=0,
        max_unconfirmed_bytes=0,
    )

    # WHEN
    payload = b"x" * 1024
    session.post(QUEUE_NAME, payload)
    session.stop()

    # THEN
    mock.post.assert_called_once_with(
        payload=payload,
        queue_uri=QUEUE_NAME,
        properties=(
            {},
            {},
        ),
        compression_algorithm_type=compression_map.get(compression),
    )


def test_session_with_invalid_compression():
    # GIVEN
    mock = sdk_mock(start=0, openQueueSync=0, post=0, stop=None)

    # WHEN
    with pytest.raises(Exception) as exc:
        Session(
            dummy_callback,
            message_compression_algorithm="something valid",
            _mock=mock,
        )

    # THEN
    assert exc.type is KeyError
