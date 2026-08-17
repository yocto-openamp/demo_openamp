#!/usr/bin/env bash
set -euo pipefail
set -x

REPO_DIR=$(dirname "$PWD")
if [[ ! -f $REPO_DIR/PROJECT_MARKER.txt ]]; then
	echo "ERROR: Start this script from the corresponding folder!" >&2
	exit 1
fi

# PRISTINE=--pristine
PRISTINE=

time docker run --rm -it \
	--user "$(id -u):$(id -g)" \
	--volume "$REPO_DIR:$REPO_DIR" \
	zephyr-dev:$(uname -m) \
	west build \
	$PRISTINE \
	--board verdin_imx8mp/mimx8ml8/m7 \
	--build-dir "$PWD/build" \
	"$PWD/zephyr" \
	-- \
	-DCONF_FILE=prj_verdin_imx8mp.conf \
	-DDTC_OVERLAY_FILE=prj_verdin_imx8mp.overlay

# ENV CCACHE_DIR=/opt/ccache
