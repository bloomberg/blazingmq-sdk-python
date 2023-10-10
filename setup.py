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
import platform
import sys

import pkgconfig
from setuptools import Extension
from setuptools import setup

# XXX: Cython imports must come after importing setuptools
from Cython.Build import cythonize  # isort:skip
from Cython.Compiler import Options  # isort:skip

IS_MAC = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

TEST_BUILD = False
if "--test-build" in sys.argv:
    TEST_BUILD = True
    sys.argv.remove("--test-build")

if os.getenv("CYTHON_TEST_MACROS", None) is not None:
    TEST_BUILD = True


COMPILER_DIRECTIVES = {
    "language_level": "3str",
    "embedsignature": True,
    "boundscheck": False,
    "wraparound": False,
    "cdivision": True,
    "linetrace": False,
    "c_string_type": "unicode",
    "c_string_encoding": "utf8",
}

DEFINE_MACROS = []

if TEST_BUILD:
    COMPILER_DIRECTIVES = {
        "language_level": "3str",
        "boundscheck": True,
        "embedsignature": True,
        "wraparound": True,
        "cdivision": False,
        "linetrace": True,
        "overflowcheck": True,
        "infer_types": True,
        "c_string_type": "unicode",
        "c_string_encoding": "utf8",
    }
    DEFINE_MACROS.extend([("CYTHON_TRACE", "1"), ("CYTHON_TRACE_NOGIL", "1")])


def create_extension(name, libraries, **kwargs):
    extra_compile_args = []

    # Enable extra warnings.
    extra_compile_args.extend(
        [
            "-Wall",
            "-Wextra",
            "-Wno-invalid-offsetof",
            "-Wno-missing-field-initializers",
            "-Wno-deprecated-declarations",
        ]
    )

    # Work around unused warning when built with old versions of Cython.
    # See https://github.com/cython/cython/issues/4948 for details.
    if sys.version_info[0:2] >= (3, 11):
        extra_compile_args.append("-DCYTHON_NCP_UNUSED=CYTHON_UNUSED")

    # Hardwire C++ flags needed for BDE bslstl support.
    extra_compile_args.extend(["-std=gnu++17", "-D_GLIBCXX_USE_CXX11_ABI=0"])

    extra_link_args = []

    if IS_LINUX:
        # Error if any of the shared libraries we link in has unresolved
        # symbols not satisfied by another library on the link line.
        extra_link_args.append("-Wl,--no-allow-shlib-undefined")

        # Hide symbols except for our required entry point.
        modname = name.rpartition(".")[-1]
        extra_link_args.append(f"-Wl,--version-script=src/blazingmq/{modname}.vers")
    elif IS_MAC:
        # Hide symbols except for our required entry point.
        modname = name.rpartition(".")[-1]
        extra_link_args.append(
            f"-Wl,-exported_symbols_list,src/blazingmq/{modname}.exp"
        )

    ext = Extension(name, **kwargs)
    ext.extra_compile_args = extra_compile_args + list(ext.extra_compile_args)
    ext.extra_link_args = extra_link_args + list(ext.extra_link_args)

    pkg_config = pkgconfig.parse(" ".join(libraries), static=True)
    ext.define_macros = list(ext.define_macros) + pkg_config["define_macros"]
    ext.include_dirs = list(ext.include_dirs) + pkg_config["include_dirs"]
    ext.library_dirs = list(ext.library_dirs) + pkg_config["library_dirs"]

    dynamic_libs = {
        "crypt",
        "dl",
        "m",
        "pthread",
        "resolv",
        "rt",
        "util",
        "z",
    }
    ext.extra_link_args += [
        f"-l{lib}" if (IS_MAC or lib in dynamic_libs) else f"-l:lib{lib}.a"
        for lib in pkg_config["libraries"]
    ]

    return ext


EXTENSIONS = [
    create_extension(
        "blazingmq._ext",
        sources=[
            "src/blazingmq/_ext.pyx",
            "src/cpp/pybmq_ballutil.cpp",
            "src/cpp/pybmq_gilacquireguard.cpp",
            "src/cpp/pybmq_gilreleaseguard.cpp",
            "src/cpp/pybmq_messageutils.cpp",
            "src/cpp/pybmq_mocksession.cpp",
            "src/cpp/pybmq_refutils.cpp",
            "src/cpp/pybmq_session.cpp",
            "src/cpp/pybmq_sessioneventhandler.cpp",
        ],
        language="c++",
        include_dirs=["src/cpp", "src"],
        libraries=["bmq"],
        define_macros=DEFINE_MACROS,
    ),
]


Options.generate_cleanup_code = 3

if not IS_LINUX and not IS_MAC:
    raise RuntimeError(f"BlazingMQ does not support this platform ({sys.platform})")

about = {}
with open("src/blazingmq/_about.py") as fp:
    exec(fp.read(), about)

setup(
    name="blazingmq",
    description="Python BlazingMQ API",
    version=about["__version__"],
    author="Bloomberg Finance LP",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Developers",
        "Operating System :: POSIX :: Linux",
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
    ],
    package_data={"blazingmq": ["py.typed", "_ext.pyi"]},
    package_dir={"": "src"},
    packages=["blazingmq"],
    ext_modules=cythonize(
        EXTENSIONS,
        include_path=["src/declarations"],
        compiler_directives=COMPILER_DIRECTIVES,
    ),
    python_requires=">=3.7",
    zip_safe=False,
)
