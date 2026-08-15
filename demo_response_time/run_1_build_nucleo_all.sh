#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f ../PROJECT_MARKER.txt ]]; then
	echo "ERROR: Start this script from the corresponding folder!" >&2
	exit 1
fi

. ../.venv/bin/activate

ZEPHYR_SDK_INSTALL_DIR="${ZEPHYR_SDK_INSTALL_DIR:-$HOME/zephyr-sdk-1.0.1}"
export ZEPHYR_SDK_INSTALL_DIR

# PRISTINE=--pristine
PRISTINE=

time west build \
    $PRISTINE \
	--board nucleo_f722ze \
	--build-dir build/nucleo_f722ze \
	zephyr \
	-- \
	-DCONF_FILE=prj_nucleo_f722ze.conf \
	-DDTC_OVERLAY_FILE=prj_nucleo_f722ze.overlay
