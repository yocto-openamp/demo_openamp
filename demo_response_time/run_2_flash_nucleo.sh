#!/usr/bin/env bash
set -euo pipefail

REPO_DIR=$(dirname "$PWD")
if [[ ! -f $REPO_DIR/PROJECT_MARKER.txt ]]; then
	echo "ERROR: Start this script from the corresponding folder!" >&2
	exit 1
fi

time docker run --rm -it \
	--workdir $PWD \
	--user "$(id -u):$(id -g)" \
	--volume "$REPO_DIR:$REPO_DIR" \
	--privileged \
	--volume /dev/bus/usb:/dev/bus/usb \
	--volume /dev/tty:/dev/tty \
	ghcr.io/yocto-openamp/zephyr-dev:$(uname -m) \
	west flash --build-dir build/nucleo --runner openocd
