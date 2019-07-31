#!/bin/bash

# Add an extra apt repository sources.list if the extra-repository argument is
# set. The extra_repository and extra_repository_key variables are filenames.
# The optional target-etc argument allows setting a different destination path
# to be able to update chroots.
# Passing the update flag will cause the script to call apt-get update at the
# end if the file was added.

EXTRA_REPOSITORY=""
EXTRA_REPOSITORY_KEY=""
TARGET_ETC="/etc"
UPDATE=0
VERBOSE=0

while [[ "$#" -ge 1 ]]; do
    case "$1" in
        --extra-repository|-e)
            shift
            EXTRA_REPOSITORY="$1"
            shift
            ;;
        --extra-repository-key|-k)
            shift
            EXTRA_REPOSITORY_KEY="$1"
            shift
            ;;
        --target-etc|-t)
            shift
            TARGET_ETC="$1"
            shift
            ;;
        --update|-u)
            UPDATE=1
            shift
            ;;
        --verbose|-v)
            VERBOSE=1
            shift
            ;;
    esac
done

if [[ "$VERBOSE" -ne 0 ]]; then
    set -x
fi

if [[ -n "${EXTRA_REPOSITORY}" ]]; then
    mkdir -p "${TARGET_ETC}"/apt/sources.list.d/
    cp "${EXTRA_REPOSITORY}" \
        "${TARGET_ETC}"/apt/sources.list.d/extra_repository.list
    if [[ -n "${EXTRA_REPOSITORY_KEY}" ]]; then
        mkdir -p "${TARGET_ETC}"/apt/trusted.gpg.d/
        cp "${EXTRA_REPOSITORY_KEY}" \
            "${TARGET_ETC}"/apt/trusted.gpg.d/extra_repository.asc
    fi
    if [[ "$UPDATE" -ne 0 ]]; then
        apt-get update
    fi
fi

