# Copyright 2026 Bloomberg Finance L.P.
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

from blazingmq._ext import AuthnCredentialCbAdapter


def test_valid_return():
    # GIVEN
    def provider():
        return ("mechanism", b"data")

    adapter = AuthnCredentialCbAdapter(provider)

    # WHEN
    result = adapter.get_credential_data()

    # THEN
    assert result == (b"mechanism", b"data")


def test_mechanism_is_encoded_as_utf8():
    # GIVEN
    def provider():
        return ("mécanisme", b"data")

    adapter = AuthnCredentialCbAdapter(provider)

    # WHEN
    result = adapter.get_credential_data()

    # THEN
    assert result == ("mécanisme".encode("utf-8"), b"data")


def test_mechanism_not_encodable():
    # GIVEN a mechanism holding a lone surrogate, which has no UTF-8 encoding
    def provider():
        return ("\ud800", b"data")

    adapter = AuthnCredentialCbAdapter(provider)

    # WHEN
    result = adapter.get_credential_data()

    # THEN
    assert result is None


def test_mechanism_with_embedded_nul_is_not_truncated():
    # GIVEN
    def provider():
        return ("PLAIN\x00extra", b"data")

    adapter = AuthnCredentialCbAdapter(provider)

    # WHEN
    result = adapter.get_credential_data()

    # THEN
    assert result == (b"PLAIN\x00extra", b"data")


def test_none_return():
    # GIVEN
    def provider():
        return None

    adapter = AuthnCredentialCbAdapter(provider)

    # WHEN
    result = adapter.get_credential_data()

    # THEN
    assert result is None


def test_not_a_tuple():
    # GIVEN
    def provider():
        return "not a tuple"

    adapter = AuthnCredentialCbAdapter(provider)

    # WHEN
    result = adapter.get_credential_data()

    # THEN
    assert result is None


def test_tuple_wrong_length():
    # GIVEN
    def provider():
        return ("mechanism", b"data", "extra")

    adapter = AuthnCredentialCbAdapter(provider)

    # WHEN
    result = adapter.get_credential_data()

    # THEN
    assert result is None


def test_mechanism_not_str():
    # GIVEN
    def provider():
        return (123, b"data")

    adapter = AuthnCredentialCbAdapter(provider)

    # WHEN
    result = adapter.get_credential_data()

    # THEN
    assert result is None


def test_data_not_bytes():
    # GIVEN
    def provider():
        return ("mechanism", "not bytes")

    adapter = AuthnCredentialCbAdapter(provider)

    # WHEN
    result = adapter.get_credential_data()

    # THEN
    assert result is None


def test_callback_raises():
    # GIVEN
    def provider():
        raise RuntimeError("broken")

    adapter = AuthnCredentialCbAdapter(provider)

    # WHEN
    result = adapter.get_credential_data()

    # THEN
    assert result is None
