#!/usr/bin/env bash
set -euox pipefail

docker save zephyr-dev:arm64 \
	| ssh -T torizon@verdin-imx8mp-08910183.local 'docker load'

