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


def test_timeouts_repr():
    # WHEN
    one = blazingmq.Timeouts(
        connect_timeout=60.0,
        disconnect_timeout=70.0,
        open_queue_timeout=80.0,
        configure_queue_timeout=90.0,
        close_queue_timeout=100.0,
    )
    # THEN
    assert (
        "Timeouts("
        "connect_timeout=60.0,"
        " disconnect_timeout=70.0,"
        " open_queue_timeout=80.0,"
        " configure_queue_timeout=90.0,"
        " close_queue_timeout=100.0)" == repr(one)
    )


def test_timeouts_default_repr():
    # WHEN
    timeouts = blazingmq.Timeouts()
    # THEN
    assert "Timeouts()" == repr(timeouts)


def test_timeouts_default_to_none():
    # WHEN
    timeouts = blazingmq.Timeouts()
    # THEN
    timeouts.connect_timeout is None
    timeouts.disconnect_timeout is None
    timeouts.open_queue_timeout is None
    timeouts.configure_queue_timeout is None
    timeouts.close_queue_timeout is None


def test_timeouts_equality():
    # GIVEN
    left = blazingmq.Timeouts()

    # WHEN
    right = blazingmq.Timeouts()

    # THEN
    assert left == right
    assert (left != right) is False


@pytest.mark.parametrize(
    "right",
    [
        None,
        "string",
        blazingmq.Timeouts(connect_timeout=60.0),
        blazingmq.Timeouts(disconnect_timeout=70.0),
        blazingmq.Timeouts(open_queue_timeout=80.0),
        blazingmq.Timeouts(configure_queue_timeout=90.0),
        blazingmq.Timeouts(close_queue_timeout=100.0),
    ],
)
def test_timeouts_other_inequality(right):
    # GIVEN
    left = blazingmq.Timeouts()

    # THEN
    assert not left == right
