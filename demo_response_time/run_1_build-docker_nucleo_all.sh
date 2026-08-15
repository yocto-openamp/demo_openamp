#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f ../PROJECT_MARKER.txt ]]; then
	echo "ERROR: Start this script from the corresponding folder!" >&2
	exit 1
fi

# PRISTINE=--pristine
PRISTINE=

time docker run --rm -it \
	--user "$(id -u):$(id -g)" \
	--env HOME=/tmp \
	-v "$PWD:/workspace" \
	zephyr-dev:$(uname -m) \
	west build \
	$PRISTINE \
	--board nucleo_f722ze \
	--build-dir build/nucleo_f722ze \
	zephyr \
	-- \
	-DUSER_CACHE_DIR=/tmp/zephyr-cache \
	-DCONF_FILE=prj_nucleo_f722ze.conf \
	-DDTC_OVERLAY_FILE=prj_nucleo_f722ze.overlay
