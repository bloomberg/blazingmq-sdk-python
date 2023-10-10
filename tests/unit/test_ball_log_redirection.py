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

import os
import subprocess
import sys
import textwrap

import pytest


@pytest.mark.parametrize(
    "diagnostics_enabled,logger_level,emitted",
    [(True, "DEBUG", True), (True, "INFO", False), (False, "DEBUG", False)],
)
def test_ball_logger_redirection(diagnostics_enabled, logger_level, emitted):
    # GIVEN
    program = textwrap.dedent(
        """
        import blazingmq._ext
        import logging
        logging.basicConfig(level='%s')
    """
        % logger_level
    )

    env = os.environ.copy()
    if diagnostics_enabled:
        env["_PYBMQ_ENABLE_DIAGNOSTICS"] = "1"
    else:
        env.pop("_PYBMQ_ENABLE_DIAGNOSTICS", None)

    process = subprocess.Popen(
        [sys.executable, "-c", program],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    # WHEN
    stdout, stderr = process.communicate()

    # THEN
    msg = b"DEBUG:blazingmq.pybmq_ballutil:Shutting down BALL redirection"
    assert (msg in stderr) is emitted


def test_ball_logger_python_exception_handling():
    # GIVEN
    program = textwrap.dedent(
        """
        import blazingmq._ext
        import logging
        logging.basicConfig(level="DEBUG")
        logging.setLogRecordFactory("something not callable")
        """
    )

    env = os.environ.copy()
    env["_PYBMQ_ENABLE_DIAGNOSTICS"] = "1"
    process = subprocess.Popen(
        [sys.executable, "-c", program],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    # WHEN
    stdout, stderr = process.communicate()

    # THEN
    assert b"Exception ignored in: 'BlazingMQ C++ log observer'" in stderr
