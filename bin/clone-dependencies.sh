#!/usr/bin/env bash

# This script clones the dependencies of the BlazingMQ Python SDK that are not
# in a package manager.  This script should not be run by users directly, but
# is instead sourced by the `./build-*.sh` scripts in this directory.


set -e
set -u
[ -z "$BASH" ] || shopt -s expand_aliases


# These are the release tags for each of the dependencies we manually clone.
# Update these to update the version of each dependency we build against.
BDE_TOOLS_TAG=3.124.0.0
BDE_TAG=3.124.0.0
NTF_CORE_TAG=latest
BLAZINGMQ_TAG=BMQBRKR_0.90.20


if [ ! -d "${DIR_THIRDPARTY}/bde-tools" ]; then
    git clone                                                                  \
        --depth 1                                                              \
        --branch ${BDE_TOOLS_TAG}                                              \
        https://github.com/bloomberg/bde-tools                                 \
        "${DIR_THIRDPARTY}/bde-tools"
fi

if [ ! -d "${DIR_THIRDPARTY}/bde" ]; then
    git clone                                                                  \
        --depth 1                                                              \
        --branch ${BDE_TAG}                                                    \
        https://github.com/bloomberg/bde.git                                   \
        "${DIR_THIRDPARTY}/bde"
fi

if [ ! -d "${DIR_THIRDPARTY}/ntf-core" ]; then
    git clone                                                                  \
        --depth 1                                                              \
        --branch ${NTF_CORE_TAG}                                               \
        https://github.com/bloomberg/ntf-core.git                              \
        "${DIR_THIRDPARTY}/ntf-core"
fi

if [ ! -d "${DIR_THIRDPARTY}/blazingmq" ]; then
    git clone                                                                  \
        --depth 1                                                              \
        --branch ${BLAZINGMQ_TAG}                                              \
        https://github.com/bloomberg/blazingmq.git                             \
        "${DIR_THIRDPARTY}/blazingmq"
fi
