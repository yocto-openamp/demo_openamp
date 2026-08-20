#!/usr/bin/env bash
set -euo pipefail

REPO_DIR=$(dirname "$PWD")
if [[ ! -f $REPO_DIR/PROJECT_MARKER.txt ]]; then
	echo "ERROR: Start this script from the corresponding folder!" >&2
	exit 1
fi

# PRISTINE=--pristine
PRISTINE=

time docker run --rm -it \
    --workdir $PWD \
	--user "$(id -u):$(id -g)" \
	--volume "$REPO_DIR:$REPO_DIR" \
	ghcr.io/yocto-openamp/zephyr-dev:$(uname -m) \
	west build \
	$PRISTINE \
	--board verdin_imx8mp/mimx8ml8/m7 \
	--build-dir build/imx8mp \
	zephyr \
	-- \
	-DCONF_FILE=prj_verdin_imx8mp.conf \
	-DDTC_OVERLAY_FILE=prj_verdin_imx8mp.overlay
