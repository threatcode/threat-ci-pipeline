#!/bin/bash
# Copyright salsa-ci-team and others
# SPDX-License-Identifier: FSFAP
# Copying and distribution of this file, with or without modification, are
# permitted in any medium without royalty provided the copyright notice and
# this notice are preserved. This file is offered as-is, without any warranty.
set -e

export TMPDIR=/tmp/build-deps
mkdir -p "${TMPDIR}"

echo " -> Starting installing the build-deps"

mk-build-deps ${HOST_ARCH:+--host-arch=${HOST_ARCH} -Pcross,nocheck} $1/debian/control

FILENAME=$(echo ${TMPDIR}/*-build-deps*.deb)
if [ ! -f "${FILENAME}" ]; then
    FILENAME=$(echo *-build-deps*.deb)
fi

PKGNAME=$(dpkg-deb -f "${FILENAME}" Package)

dpkg --force-depends --force-conflicts -i "${FILENAME}"

aptitude -y --without-recommends \
	-o "Dpkg::Options::=--force-confold" \
	-o "APT::Install-Recommends=false" \
	-o "Aptitude::ProblemResolver::StepScore=100" \
	-o "Aptitude::ProblemResolver::SolutionCost=safety, priority, non-default-versions" \
	-o "Aptitude::ProblemResolver::Hints::KeepDummy=reject $PKGNAME :UNINST" \
	-o "Aptitude::ProblemResolver::Keep-All-Level=55000" \
	-o "Aptitude::ProblemResolver::Remove-Essential-Level=maximum" \
	install "${PKGNAME}${HOST_ARCH:+:${HOST_ARCH}}"

rm $FILENAME

if ! dpkg -l "${PKGNAME}" 2>/dev/null | grep -q ^ii; then
	echo "Aptitude couldn't satisfy the build dependencies"
	exit 1
fi
echo " -> Finished installing the build-deps"
