#!/usr/bin/env bash

# This script builds BlazingMQ and all of its dependencies for MacOS 11.0.
#
# Before running this script, install following prerequisites, if not present
# yet, by copy-and-pasting the commands between `<<PREREQUISITES` and
# `PREREQUISITES` below:
                                                    # shellcheck disable=SC2188
<<PREREQUISITES
brew install \
    curl \
    pkgconfig \
    ninja \
    flex \
    zlib \
    bison \
    flex \
    google-benchmark \
    cmake
PREREQUISITES

set -e
set -u
[ -z "$BASH" ] || shopt -s expand_aliases

# :: Set some initial constants :::::::::::::::::::::::::::::::::::::::::::::::
DIR_ROOT="$(pwd)"

DIR_THIRDPARTY="${DIR_ROOT}/thirdparty"
mkdir -p "${DIR_THIRDPARTY}"

DIR_BUILD="${DIR_BUILD:-${DIR_ROOT}/build}"
mkdir -p "${DIR_BUILD}"

DIR_INSTALL="${DIR_INSTALL:-${DIR_ROOT}/install}"
mkdir -p "${DIR_INSTALL}"

script_path="bin/$(basename "$0")"

if [ ! -f "$script_path" ] || [ "$(realpath "$0")" != "$(realpath "$script_path")" ]; then
    echo 'This script must be run from the root of the BlazingMQ repository.'
    exit 1
fi

# :: Clone dependencies :::::::::::::::::::::::::::::::::::::::::::::::::::::::

if [ ! -d "${DIR_THIRDPARTY}/bde-tools" ]; then
    git clone https://github.com/bloomberg/bde-tools "${DIR_THIRDPARTY}/bde-tools"
fi
if [ ! -d "${DIR_THIRDPARTY}/bde" ]; then
    git clone --depth 1 https://github.com/bloomberg/bde.git "${DIR_THIRDPARTY}/bde"
fi
if [ ! -d "${DIR_THIRDPARTY}/ntf-core" ]; then
    git clone --depth 1 https://github.com/bloomberg/ntf-core.git "${DIR_THIRDPARTY}/ntf-core"
fi
if [ ! -d "${DIR_THIRDPARTY}/blazingmq" ]; then
    git clone --depth 1 https://github.com/bloomberg/blazingmq.git "${DIR_THIRDPARTY}/blazingmq"
fi

# Build and install BDE
# Refer to https://bloomberg.github.io/bde/library_information/build.html
PATH="${DIR_THIRDPARTY}/bde-tools/bin:$PATH"

if [ ! -e "${DIR_BUILD}/bde/.complete" ]; then
    pushd "${DIR_THIRDPARTY}/bde"
    eval "$(bbs_build_env -u opt_64_pic_cpp17 -b "${DIR_BUILD}/bde" -i ${DIR_INSTALL})"
    bbs_build configure --prefix="${DIR_INSTALL}"
    bbs_build build -j 16
    bbs_build install --install_dir "/" --prefix="${DIR_INSTALL}"
    eval "$(bbs_build_env unset)"
    popd
    touch "${DIR_BUILD}/bde/.complete"
fi

if [ ! -e "${DIR_BUILD}/ntf-core/.complete" ]; then
    # Build and install NTF
    pushd "${DIR_THIRDPARTY}/ntf-core"
    ./configure --prefix "${DIR_INSTALL}" \
        --output "${DIR_BUILD}/ntf-core" \
        --ufid opt_64_pic_cpp17 \
        --generator "Ninja" \
        --without-warnings-as-errors \
        --without-usage-examples \
        --without-applications
    make -j 16
    make install
    popd
    touch "${DIR_BUILD}/ntf-core/.complete"
fi

# Determine paths based on Intel vs Apple Silicon CPU
if [ "$(uname -p)" == 'arm' ]; then
    BREW_PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:/opt/homebrew/opt/zlib/lib/pkgconfig"
    FLEX_ROOT="/opt/homebrew/opt/flex"
else
    BREW_PKG_CONFIG_PATH="/usr/local/lib/pkgconfig:/usr/local/opt/zlib/lib/pkgconfig"
    FLEX_ROOT="/usr/local/opt/flex"
fi

# :: Build the BlazingMQ repo :::::::::::::::::::::::::::::::::::::::::::::::::::::::
if [ ! -e "${DIR_BUILD}/blazingmq/.complete" ]; then
    pushd "${DIR_THIRDPARTY}/blazingmq"
    export PKG_CONFIG_PATH="${DIR_INSTALL}/lib/pkgconfig:${BREW_PKG_CONFIG_PATH}"
    CMAKE_OPTIONS=(\
        -DBDE_BUILD_TARGET_64=1 \
        -DBDE_BUILD_TARGET_CPP17=ON \
        -DCMAKE_BUILD_TYPE=RelWithDebInfo \
        -DINSTALL_TARGETS="bmqbrkr;bmq;mwc" \
        -DCMAKE_INSTALL_LIBDIR="lib" \
        -DCMAKE_INSTALL_PREFIX="${DIR_INSTALL}" \
        -DCMAKE_MODULE_PATH="${DIR_ROOT}" \
        -DCMAKE_PREFIX_PATH="${DIR_THIRDPARTY}/bde-tools" \
        -DCMAKE_TOOLCHAIN_FILE="${DIR_THIRDPARTY}/bde-tools/BdeBuildSystem/toolchains/darwin/gcc-default.cmake" \
        -DFLEX_ROOT="${FLEX_ROOT}"
        -G "Ninja")
    cmake -B "${DIR_BUILD}/blazingmq" -S "." "${CMAKE_OPTIONS[@]}"
    cmake --build "${DIR_BUILD}/blazingmq" -j 16 --target bmq
    cmake --install "${DIR_BUILD}/blazingmq" --component mwc-all
    cmake --install "${DIR_BUILD}/blazingmq" --component bmq-all
    popd
    touch "${DIR_BUILD}/blazingmq/.complete"
fi
