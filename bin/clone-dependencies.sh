#!/usr/bin/env bash

# This script clones the dependencies of the BlazingMQ Python SDK that are not
# in a package manager.  This script should not be run by users directly, but
# is instead sourced by the `./build-*.sh` scripts in this directory.


set -e
set -u
[ -z "$BASH" ] || shopt -s expand_aliases


# These are the release tags for each of the dependencies we manually clone.
# Update these to update the version of each dependency we build against.
BDE_TOOLS_TAG=4.32.0.0
BDE_TAG=4.32.0.0
NTF_CORE_TAG=2.6.6
BLAZINGMQ_TAG=v0.95.14


if [ ! -d "${DIR_THIRDPARTY}/bde-tools" ]; then
    git clone                                                                  \
        https://github.com/bloomberg/bde-tools                                 \
        "${DIR_THIRDPARTY}/bde-tools"
    git -C "${DIR_THIRDPARTY}/bde-tools" checkout ${BDE_TOOLS_TAG}
fi

if [ ! -d "${DIR_THIRDPARTY}/bde" ]; then
    git clone                                                                  \
        https://github.com/bloomberg/bde.git                                   \
        "${DIR_THIRDPARTY}/bde"
    git -C "${DIR_THIRDPARTY}/bde" checkout ${BDE_TAG}
fi

if [ ! -d "${DIR_THIRDPARTY}/ntf-core" ]; then
    git clone                                                                  \
        https://github.com/bloomberg/ntf-core.git                              \
        "${DIR_THIRDPARTY}/ntf-core"
    git -C "${DIR_THIRDPARTY}/ntf-core" checkout ${NTF_CORE_TAG}
fi

if [ ! -d "${DIR_THIRDPARTY}/blazingmq" ]; then
    git clone                                                                  \
        https://github.com/bloomberg/blazingmq.git                             \
        "${DIR_THIRDPARTY}/blazingmq"
    git -C "${DIR_THIRDPARTY}/blazingmq" checkout ${BLAZINGMQ_TAG}
fi
