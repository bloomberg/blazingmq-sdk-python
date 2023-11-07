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

import pytest

import blazingmq
from blazingmq import exceptions


def test_bad_queue_uri(default_session, zeroed_queue_options):
    # GIVEN
    # WHEN
    with pytest.raises(Exception) as exc:
        default_session.open_queue(
            "tcp://localhost:30114",
            read=True,
            write=True,
            options=zeroed_queue_options,
        )

    # THEN
    assert exc.type is exceptions.Error
    assert exc.match("Failed to open tcp://localhost:30114 queue: INVALID_URI: .+")


def test_open_after_stop(default_session, unique_queue, zeroed_queue_options):
    # GIVEN
    default_session.stop()

    # WHEN
    with pytest.raises(Exception) as exc:
        default_session.open_queue(
            unique_queue,
            read=True,
            write=True,
            options=zeroed_queue_options,
            timeout=1,
        )

    # THEN
    assert exc.type is exceptions.Error
    assert exc.match("Method called after session was stopped")


def test_close_after_stop(default_session, unique_queue, zeroed_queue_options):
    # GIVEN
    default_session.open_queue(
        unique_queue,
        read=True,
        write=True,
        options=zeroed_queue_options,
        timeout=1,
    )
    default_session.stop()

    # WHEN
    with pytest.raises(Exception) as exc:
        default_session.close_queue(unique_queue, timeout=1)

    # THEN
    assert exc.type is exceptions.Error
    assert exc.match("Method called after session was stopped")


def test_open_queue_raises_invalid_flags(
    default_session, unique_queue, zeroed_queue_options
):
    # GIVEN
    # WHEN
    with pytest.raises(Exception) as exc:
        default_session.open_queue(
            unique_queue,
            read=False,
            write=False,
            options=zeroed_queue_options,
            timeout=1,
        )

    # THEN
    assert exc.type is exceptions.Error
    assert exc.match(
        "Failed to open bmq://bmq.test.mmap.priority.+ queue: INVALID_FLAGS: .+"
    )


def test_open_write_queue_options_ignored(
    default_session, unique_queue, zeroed_queue_options
):
    # GIVEN
    default_session.open_queue(
        unique_queue,
        read=False,
        write=True,
        options=zeroed_queue_options,
    )

    # WHEN
    options = default_session.get_queue_options(unique_queue)

    # THEN
    assert options != zeroed_queue_options


def test_open_queue_raises_negative_unconfirmed_messages(default_session, unique_queue):
    # GIVEN
    # WHEN
    with pytest.raises(Exception) as exc:
        default_session.open_queue(
            unique_queue,
            read=True,
            write=True,
            options=blazingmq.QueueOptions(
                consumer_priority=0,
                max_unconfirmed_messages=-1,
                max_unconfirmed_bytes=0,
            ),
            timeout=1,
        )

    # THEN
    assert exc.type is exceptions.Error
    assert exc.match(
        "Failed to open bmq://bmq.test.mmap.priority.+ queue: INVALID_ARGUMENT: .+"
    )


def test_open_queue_raises_negative_unconfirmed_bytes(default_session, unique_queue):
    # GIVEN
    # WHEN
    with pytest.raises(Exception) as exc:
        default_session.open_queue(
            unique_queue,
            read=True,
            write=True,
            options=blazingmq.QueueOptions(
                consumer_priority=0,
                max_unconfirmed_messages=0,
                max_unconfirmed_bytes=-1,
            ),
            timeout=1,
        )

    # THEN
    assert exc.type is exceptions.Error
    assert exc.match(
        "Failed to open bmq://bmq.test.mmap.priority.+ queue: INVALID_ARGUMENT: .+"
    )


def test_open_queue_does_not_raise_negative_consumer_priority(
    default_session, unique_queue
):
    # GIVEN
    # WHEN
    default_session.open_queue(
        unique_queue,
        read=True,
        write=True,
        options=blazingmq.QueueOptions(
            max_unconfirmed_messages=0,
            max_unconfirmed_bytes=0,
            consumer_priority=-1,
        ),
        timeout=1,
    )

    # THEN
    # we didn't raise!


@pytest.mark.parametrize("consumer_priority", [-(2**31), 2**31 - 1])
def test_open_queue_raises_invalid_consumer_priority(
    consumer_priority, default_session, unique_queue
):
    # GIVEN
    # WHEN
    with pytest.raises(Exception) as exc:
        default_session.open_queue(
            unique_queue,
            read=True,
            write=True,
            options=blazingmq.QueueOptions(
                max_unconfirmed_messages=0,
                max_unconfirmed_bytes=0,
                consumer_priority=consumer_priority,
            ),
            timeout=1,
        )

    # THEN
    assert exc.type is exceptions.Error
    assert exc.match(
        "Failed to open bmq://bmq.test.mmap.priority.+ queue: INVALID_ARGUMENT: .+"
    )


@pytest.mark.parametrize("consumer_priority", [-(2**31), 2**31 - 1])
def test_configure_queue_raises_invalid_consumer_priority(
    consumer_priority, default_session, unique_queue
):
    # GIVEN
    default_session.open_queue(
        unique_queue,
        read=True,
        write=True,
        options=blazingmq.QueueOptions(
            consumer_priority=1,
            max_unconfirmed_messages=0,
            max_unconfirmed_bytes=0,
        ),
    )
    # WHEN
    with pytest.raises(Exception) as exc:
        default_session.configure_queue(
            unique_queue,
            options=blazingmq.QueueOptions(
                consumer_priority=consumer_priority,
                max_unconfirmed_messages=0,
                max_unconfirmed_bytes=0,
            ),
        )
    # THEN
    assert exc.type is exceptions.Error
    assert exc.match(
        "Failed to configure bmq://bmq.test.mmap.priority.+ queue: INVALID_ARGUMENT: .+"
    )


def test_configure_queue_bad_uri(default_session, unique_queue):
    # GIVEN
    default_session.open_queue(
        unique_queue,
        read=True,
        write=True,
        options=blazingmq.QueueOptions(
            consumer_priority=1,
            max_unconfirmed_messages=0,
            max_unconfirmed_bytes=0,
        ),
    )
    # WHEN
    with pytest.raises(Exception) as exc:
        default_session.configure_queue(
            "tcp://localhost:30114",
            options=blazingmq.QueueOptions(
                consumer_priority=1,
                max_unconfirmed_messages=0,
                max_unconfirmed_bytes=0,
            ),
        )
    # THEN
    assert exc.type is exceptions.Error
    assert exc.match(r"^Queue not opened$")


def test_configure_queue_raises_invalid_max_unconfirmed_messages(
    default_session, unique_queue
):
    # GIVEN
    default_session.open_queue(
        unique_queue,
        read=True,
        write=True,
        options=blazingmq.QueueOptions(
            consumer_priority=1,
            max_unconfirmed_messages=0,
            max_unconfirmed_bytes=0,
        ),
    )
    # WHEN
    with pytest.raises(Exception) as exc:
        default_session.configure_queue(
            unique_queue,
            options=blazingmq.QueueOptions(
                consumer_priority=1,
                max_unconfirmed_messages=-1,
                max_unconfirmed_bytes=0,
            ),
        )
    # THEN
    assert exc.type is exceptions.Error
    assert exc.match(
        "Failed to configure bmq://bmq.test.mmap.priority.+ queue: INVALID_ARGUMENT: .+"
    )


def test_configure_queue_raises_invalid_max_unconfirmed_bytes(
    default_session, unique_queue
):
    # GIVEN
    default_session.open_queue(
        unique_queue,
        read=True,
        write=True,
        options=blazingmq.QueueOptions(
            consumer_priority=1,
            max_unconfirmed_messages=0,
            max_unconfirmed_bytes=0,
        ),
    )
    # WHEN
    with pytest.raises(Exception) as exc:
        default_session.configure_queue(
            unique_queue,
            options=blazingmq.QueueOptions(
                consumer_priority=1,
                max_unconfirmed_messages=0,
                max_unconfirmed_bytes=-1,
            ),
        )
    # THEN
    assert exc.type is exceptions.Error
    assert exc.match(
        "Failed to configure bmq://bmq.test.mmap.priority.+ queue: INVALID_ARGUMENT: .+"
    )


def test_default_options_returned(default_session, unique_queue):
    # GIVEN
    unset_options = blazingmq.QueueOptions()
    default_options = blazingmq.QueueOptions(
        max_unconfirmed_messages=blazingmq.QueueOptions.DEFAULT_MAX_UNCONFIRMED_MESSAGES,
        max_unconfirmed_bytes=blazingmq.QueueOptions.DEFAULT_MAX_UNCONFIRMED_BYTES,
        consumer_priority=blazingmq.QueueOptions.DEFAULT_CONSUMER_PRIORITY,
        suspends_on_bad_host_health=blazingmq.QueueOptions.DEFAULT_SUSPENDS_ON_BAD_HOST_HEALTH,
    )

    # WHEN
    default_session.open_queue(unique_queue, read=True, options=unset_options)
    gotten_opts = default_session.get_queue_options(unique_queue)

    # THEN
    assert gotten_opts == default_options


def test_open_options_returned(health_aware_session, unique_queue):
    # GIVEN
    base_options = blazingmq.QueueOptions(
        max_unconfirmed_messages=1,
        max_unconfirmed_bytes=2,
        consumer_priority=3,
        suspends_on_bad_host_health=True,
    )

    # WHEN
    health_aware_session.open_queue(unique_queue, read=True, options=base_options)
    gotten_opts = health_aware_session.get_queue_options(unique_queue)

    # THEN
    assert gotten_opts == base_options


def test_configure_options_returned(default_session, unique_queue):
    # GIVEN
    base_options = blazingmq.QueueOptions(
        max_unconfirmed_messages=1,
        max_unconfirmed_bytes=2,
        consumer_priority=3,
    )
    config_options = blazingmq.QueueOptions(
        max_unconfirmed_messages=10,
        max_unconfirmed_bytes=20,
        consumer_priority=30,
        suspends_on_bad_host_health=False,
    )

    # WHEN
    default_session.open_queue(unique_queue, read=True, options=base_options)
    default_session.configure_queue(unique_queue, options=config_options)
    gotten_opts = default_session.get_queue_options(unique_queue)

    # THEN
    assert gotten_opts == config_options


def test_changing_suspension_behavior(health_aware_session, unique_queue):
    # GIVEN
    base_options = blazingmq.QueueOptions(
        max_unconfirmed_messages=1,
        max_unconfirmed_bytes=2,
        consumer_priority=3,
        suspends_on_bad_host_health=True,
    )
    config_options = blazingmq.QueueOptions(
        max_unconfirmed_messages=1,
        max_unconfirmed_bytes=2,
        consumer_priority=3,
        suspends_on_bad_host_health=False,
    )

    # WHEN
    health_aware_session.open_queue(unique_queue, read=True, options=base_options)
    health_aware_session.configure_queue(unique_queue, options=config_options)
    gotten_opts = health_aware_session.get_queue_options(unique_queue)

    # THEN
    assert gotten_opts == config_options


def test_bad_configure_leaves_options_intact(health_aware_session, unique_queue):
    # GIVEN
    base_options = blazingmq.QueueOptions(
        max_unconfirmed_messages=1,
        max_unconfirmed_bytes=2,
        consumer_priority=3,
        suspends_on_bad_host_health=True,
    )
    bad_options = blazingmq.QueueOptions(
        max_unconfirmed_messages=-1,
        max_unconfirmed_bytes=-1,
        consumer_priority=30,
    )
    health_aware_session.open_queue(unique_queue, read=True, options=base_options)
    with pytest.raises(exceptions.Error):
        health_aware_session.configure_queue(unique_queue, options=bad_options)

    # WHEN
    gotten_opts = health_aware_session.get_queue_options(unique_queue)

    # THEN
    assert gotten_opts == base_options


def test_bad_uri_for_queue_options(default_session):
    # WHEN
    with pytest.raises(Exception) as exc:
        default_session.get_queue_options("nonexistent queue")

    # THEN
    exc.type is exceptions.Error
    exc.match("Queue not opened")


def test_get_on_stop_fails(default_session, unique_queue):
    # GIVEN
    default_session.open_queue(unique_queue, read=True)

    # WHEN
    default_session.stop()
    with pytest.raises(Exception) as exc:
        default_session.configure_queue(unique_queue, options=blazingmq.QueueOptions())

    # THEN
    assert exc.type is exceptions.Error
    assert exc.match("Method called after session was stopped")
