#!/bin/bash

set -eu

if [ ! -d "${WORKING_DIR}" ]; then
        echo "Directory \"${WORKING_DIR}\" does not exist, aborting build."
        echo "Please check the defintion of WORKING_DIR in your gitlab-ci.yml"
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

DOCKER_IMAGE_NAME=$1

VOLUME_DIR=${CI_PROJECT_DIR:-${GBP_BUILD_DIR}}
VOLUMES="-v ${VOLUME_DIR}/..:${VOLUME_DIR}/.. -v ${CCACHE_TMP_DIR}:/tmp/ccache"

CCACHE_DIR_ENV="-e CCACHE_DIR=/tmp/ccache"

CONTAINER_ID=$(docker run -d --rm -w ${GBP_BUILD_DIR} ${VOLUMES} ${DOCKER_IMAGE_NAME} sleep infinity)

cleanup() {
    docker rm -f ${CONTAINER_ID}
}
trap cleanup EXIT

DEBIAN_VARENVS=""

IFS=$'\n' && for varenv in $(env); do
    if [[ $varenv == DEB* ]]; then
        DEBIAN_VARENVS+=" -e \"${varenv}\""
    fi
done

set -x

eval docker cp /etc/apt/sources.list.d/./ ${CONTAINER_ID}:/etc/apt/sources.list.d/

eval docker cp /etc/apt/preferences.d/./ ${CONTAINER_ID}:/etc/apt/preferences.d/

eval docker exec ${DEBIAN_VARENVS} ${CONTAINER_ID} apt-get update

eval docker exec ${DEBIAN_VARENVS} ${CONTAINER_ID} apt-get install eatmydata -y

eval docker exec ${DEBIAN_VARENVS} ${CONTAINER_ID} eatmydata apt-get dist-upgrade -y

set -o pipefail

eval docker exec ${DEBIAN_VARENVS} ${CONTAINER_ID} eatmydata install-build-deps.sh |& tee -a "${BUILD_LOGFILE}"

eval docker exec ${DEBIAN_VARENVS} ${CONTAINER_ID} eatmydata chown -R salsa-ci:100 ${GBP_BUILD_DIR}/.. /tmp/ccache

eval docker exec --user salsa-ci ${DEBIAN_VARENVS} ${CCACHE_DIR_ENV} ${CONTAINER_ID} ccache -z

eval docker exec --user salsa-ci ${DEBIAN_VARENVS} ${CCACHE_DIR_ENV} ${CONTAINER_ID} eatmydata dpkg-buildpackage "${@:2}" |& tee -a "${BUILD_LOGFILE}"

eval docker exec --user salsa-ci ${DEBIAN_VARENVS} ${CCACHE_DIR_ENV} ${CONTAINER_ID} ccache -s
