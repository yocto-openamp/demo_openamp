set -euox pipefail

docker buildx build \
  --platform linux/arm64 \
  -t zephyr-dev:arm64 \
  .
