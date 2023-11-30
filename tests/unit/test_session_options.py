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


def test_session_options_repr():
    # WHEN
    one = blazingmq.SessionOptions(
        message_compression_algorithm=blazingmq.CompressionAlgorithmType.ZLIB,
        timeouts=blazingmq.Timeouts(),
        host_health_monitor=blazingmq.BasicHealthMonitor(),
        num_processing_threads=1,
        blob_buffer_size=5000,
        channel_high_watermark=8000000,
        event_queue_watermarks=(6000000, 7000000),
        stats_dump_interval=30.0,
    )
    # THEN
    assert (
        "SessionOptions("
        "message_compression_algorithm=<CompressionAlgorithmType.ZLIB>,"
        " timeouts=Timeouts(),"
        " host_health_monitor=BasicHealthMonitor(),"
        " num_processing_threads=1,"
        " blob_buffer_size=5000,"
        " channel_high_watermark=8000000,"
        " event_queue_watermarks=(6000000, 7000000),"
        " stats_dump_interval=30.0)" == repr(one)
    )


def test_session_options_default_repr():
    # WHEN
    options = blazingmq.SessionOptions()
    # THEN
    assert "SessionOptions()" == repr(options)


def test_session_options_default_to_none():
    # WHEN
    options = blazingmq.SessionOptions()
    # THEN
    assert options.message_compression_algorithm is None
    assert options.timeouts is None
    assert options.host_health_monitor is None
    assert options.num_processing_threads is None
    assert options.blob_buffer_size is None
    assert options.channel_high_watermark is None
    assert options.event_queue_watermarks is None
    assert options.stats_dump_interval is None


def test_session_options_equality():
    # GIVEN
    left = blazingmq.SessionOptions()

    # WHEN
    right = blazingmq.SessionOptions()

    # THEN
    assert left == right
    assert (left != right) is False


@pytest.mark.parametrize(
    "right",
    [
        None,
        "string",
        blazingmq.SessionOptions(
            message_compression_algorithm=blazingmq.CompressionAlgorithmType.ZLIB
        ),
        blazingmq.SessionOptions(timeouts=blazingmq.Timeouts()),
        blazingmq.SessionOptions(host_health_monitor=blazingmq.BasicHealthMonitor()),
        blazingmq.SessionOptions(num_processing_threads=1),
        blazingmq.SessionOptions(blob_buffer_size=5000),
        blazingmq.SessionOptions(channel_high_watermark=8000000),
        blazingmq.SessionOptions(event_queue_watermarks=(6000000, 7000000)),
        blazingmq.SessionOptions(stats_dump_interval=30.0),
    ],
)
def test_queue_options_other_inequality(right):
    # GIVEN
    left = blazingmq.SessionOptions()

    # THEN
    assert not left == right
