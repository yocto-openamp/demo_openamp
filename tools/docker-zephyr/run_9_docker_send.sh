#!/usr/bin/env bash
set -euox pipefail

docker save zephyr-dev:aarch64 \
	| ssh -T torizon@verdin-imx8mp-08910183.local 'docker load'

