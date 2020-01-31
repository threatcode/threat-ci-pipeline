#!/bin/bash
# Copyright salsa-ci-team and others
# SPDX-License-Identifier: FSFAP
# Copying and distribution of this file, with or without modification, are
# permitted in any medium without royalty provided the copyright notice and
# this notice are preserved. This file is offered as-is, without any warranty.

set -eu

if [ ! -d "${WORKING_DIR}" ]; then
        echo "Directory \"${WORKING_DIR}\" does not exist, aborting."
        echo "Please check the defintion of WORKING_DIR in your salsa-ci.yml"
        echo "It should look like this:"
        echo "  WORKING_DIR: \$CI_PROJECT_DIR/debian/output"
        echo "See the top of https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml"
        echo "for an example."
        exit 1
fi

DOCKER_IMAGE_NAME=$1

VOLUME_DIR=${CI_PROJECT_DIR:-$(pwd)}
VOLUMES="-v ${VOLUME_DIR}/..:${VOLUME_DIR}/.."

CONTAINER_ID=$(docker run -d --rm -w ${VOLUME_DIR} ${VOLUMES} ${DOCKER_IMAGE_NAME} sleep infinity)

cleanup() {
    docker rm -f ${CONTAINER_ID}
}
trap cleanup EXIT

set -x

docker cp /etc/apt/sources.list.d/./ ${CONTAINER_ID}:/etc/apt/sources.list.d/

docker cp /etc/apt/trusted.gpg.d/./ ${CONTAINER_ID}:/etc/apt/trusted.gpg.d/

docker cp /etc/apt/preferences.d/./ ${CONTAINER_ID}:/etc/apt/preferences.d/

docker exec ${CONTAINER_ID} sed -n '/^deb\s/s//deb-src /p' /etc/apt/sources.list > /etc/apt/sources.list.d/deb-src.list

docker exec ${CONTAINER_ID} apt-get update

docker exec ${CONTAINER_ID} apt-get install -y devscripts

docker exec ${CONTAINER_ID} origtargz -dt

mv ../*.orig.* ${WORKING_DIR}
