#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f ../PROJECT_MARKER.txt ]]; then
	echo "ERROR: Start this script from the corresponding folder!" >&2
	exit 1
fi

# PRISTINE=--pristine
PRISTINE=
# -DUSER_CACHE_DIR=/workspace/build/.cache \

time docker run --rm -it \
	--user "$(id -u):$(id -g)" \
	--env HOME=/tmp \
	--env CCACHE_DIR=/workspace/build/.ccache \
	-v "$PWD:/workspace" \
	zephyr-dev:$(uname -m) \
	west build \
	$PRISTINE \
	--board verdin_imx8mp/mimx8ml8/m7 \
	--build-dir build \
	zephyr \
	-- \
	-DCONF_FILE=prj_verdin_imx8mp.conf \
	-DDTC_OVERLAY_FILE=prj_verdin_imx8mp.overlay
