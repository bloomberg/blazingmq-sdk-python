// Copyright 2019-2026 Bloomberg Finance L.P.
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

#ifndef INCLUDED_PYBMQ_SESSIONCONFIG
#define INCLUDED_PYBMQ_SESSIONCONFIG

#include <bmqt_compressionalgorithmtype.h>

#include <bsl_optional.h>
#include <bsl_utility.h>
#include <bsls_timeinterval.h>

namespace BloombergLP {
namespace pybmq {

// ===================
// struct SessionConfig
// ===================

/// The options a `pybmq::Session` is constructed with, other than its Python
/// callbacks and host health monitor.
///
/// A default-constructed `SessionConfig` means "no option set": empty
/// optionals, and default-constructed `bsls::TimeInterval`s, which
/// `Session` treats as unset.  A new option can therefore be added as a
/// field without changing any existing call site.
///
/// `broker_uri` and `script_name` are held, not owned, and must outlive the
/// `Session` constructor call.
struct SessionConfig
{
    // PUBLIC DATA
    const char* broker_uri;
    const char* script_name;
    bmqt::CompressionAlgorithmType::Enum message_compression_type;
    bsl::optional<int> num_processing_threads;
    bsl::optional<int> blob_buffer_size;
    bsl::optional<int> channel_high_watermark;
    bsl::optional<bsl::pair<int, int> > event_queue_watermarks;
    bsls::TimeInterval stats_dump_interval;
    bsls::TimeInterval connect_timeout;
    bsls::TimeInterval disconnect_timeout;
    bsls::TimeInterval open_queue_timeout;
    bsls::TimeInterval configure_queue_timeout;
    bsls::TimeInterval close_queue_timeout;
    bool monitor_host_health;

    // CREATORS
    SessionConfig();
};

// ===========================================================================
//                              INLINE DEFINITIONS
// ===========================================================================

inline SessionConfig::SessionConfig()
: broker_uri(0)
, script_name(0)
, message_compression_type(bmqt::CompressionAlgorithmType::e_NONE)
, num_processing_threads()
, blob_buffer_size()
, channel_high_watermark()
, event_queue_watermarks()
, stats_dump_interval()
, connect_timeout()
, disconnect_timeout()
, open_queue_timeout()
, configure_queue_timeout()
, close_queue_timeout()
, monitor_host_health(false)
{
}

}  // namespace pybmq
}  // namespace BloombergLP

#endif
