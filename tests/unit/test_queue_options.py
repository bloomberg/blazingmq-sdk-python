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


def test_queue_options_repr():
    # WHEN
    one = blazingmq.QueueOptions(
        consumer_priority=100,
        max_unconfirmed_bytes=1,
        max_unconfirmed_messages=10,
        suspends_on_bad_host_health=False,
    )
    # THEN
    assert (
        "QueueOptions("
        "max_unconfirmed_messages=10,"
        " max_unconfirmed_bytes=1,"
        " consumer_priority=100,"
        " suspends_on_bad_host_health=False)" == repr(one)
    )


def test_queue_options_default_repr():
    # WHEN
    options = blazingmq.QueueOptions()
    # THEN
    assert "QueueOptions()" == repr(options)


def test_queue_options_default_to_none():
    # WHEN
    options = blazingmq.QueueOptions()
    # THEN
    options.consumer_priority is None
    options.max_unconfirmed_bytes is None
    options.max_unconfirmed_messages is None
    options.suspends_on_bad_host_health is None


def test_queue_options_equality():
    # GIVEN
    left = blazingmq.QueueOptions()

    # WHEN
    right = blazingmq.QueueOptions()

    # THEN
    assert left == right
    assert (left != right) is False


@pytest.mark.parametrize(
    "right",
    [
        None,
        "string",
        blazingmq.QueueOptions(max_unconfirmed_messages=1),
        blazingmq.QueueOptions(max_unconfirmed_bytes=1),
        blazingmq.QueueOptions(consumer_priority=1),
    ],
)
def test_queue_options_other_inequality(right):
    # GIVEN
    left = blazingmq.QueueOptions()

    # THEN
    assert not left == right
