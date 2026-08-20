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
	--board nucleo_f722ze \
	--build-dir build/nucleo  \
	zephyr \
	-- \
	-DCONF_FILE=prj_nucleo_f722ze.conf \
	-DDTC_OVERLAY_FILE=prj_nucleo_f722ze.overlay
