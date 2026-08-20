set -euox pipefail

docker buildx build \
  -t ghcr.io/yocto-openamp/zephyr-dev:x86_64 \
  -t zephyr-dev:x86_64 \
  .
