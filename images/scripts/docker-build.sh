#!/bin/bash
# Copyright salsa-ci-team and others
# SPDX-License-Identifier: FSFAP
# Copying and distribution of this file, with or without modification, are
# permitted in any medium without royalty provided the copyright notice and
# this notice are preserved. This file is offered as-is, without any warranty.

set -eu

if [ ! -d "${WORKING_DIR}" ]; then
        echo "Directory \"${WORKING_DIR}\" does not exist, aborting build."
        echo "Please check the defintion of WORKING_DIR in your salsa-ci.yml"
        echo "It should look like this:"
        echo "  WORKING_DIR: \$CI_PROJECT_DIR/debian/output"
        echo "See the top of https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml"
        echo "for an example."
        exit 1
fi

BUILD_LOGFILE_SOURCE=$(dpkg-parsechangelog -S Source)
BUILD_LOGFILE_VERSION=$(dpkg-parsechangelog -S Version)
BUILD_LOGFILE_VERSION=${BUILD_LOGFILE_VERSION#*:}
BUILD_LOGFILE_ARCH=$(dpkg --print-architecture)

BUILD_LOGFILE="${WORKING_DIR}/${BUILD_LOGFILE_SOURCE}_${BUILD_LOGFILE_VERSION}_${BUILD_LOGFILE_ARCH}.build"

CCACHE_DIR_ENV="CCACHE_DIR=/tmp/ccache"

DEBIAN_VARENVS=""

IFS=$'\n' && for varenv in $(env); do
    if [[ $varenv == DEB* ]]; then
        DEBIAN_VARENVS+=" -e \"${varenv}\""
    fi
done

set -x

apt-get update

apt-get install eatmydata -y

eatmydata apt-get dist-upgrade -y

set -o pipefail

eatmydata install-build-deps.sh |& tee -a "${BUILD_LOGFILE}"

${CCACHE_DIR_ENV}  ccache -z

${CCACHE_DIR_ENV}  eatmydata dpkg-buildpackage "${@:1}" |& tee -a "${BUILD_LOGFILE}"

${CCACHE_DIR_ENV}  ccache -s
