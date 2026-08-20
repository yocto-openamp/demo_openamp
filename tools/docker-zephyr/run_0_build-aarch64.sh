set -euox pipefail

docker buildx build \
  --platform linux/arm64 \
  -t ghcr.io/yocto-openamp/zephyr-dev:aarch64 \
  -t zephyr-dev:aarch64 \
  .
