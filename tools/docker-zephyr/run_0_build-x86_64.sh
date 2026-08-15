set -euox pipefail

docker buildx build \
  -t zephyr-dev:x86_64 \
  .
