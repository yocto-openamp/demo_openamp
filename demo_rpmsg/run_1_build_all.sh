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
	--board verdin_imx8mp/mimx8ml8/m7 \
	--build-dir build \
	zephyr \
	-- \
	-DCONF_FILE=prj_verdin_imx8mp.conf \
	-DDTC_OVERLAY_FILE=prj_verdin_imx8mp.overlay
