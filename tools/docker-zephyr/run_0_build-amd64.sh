set -euox pipefail

docker buildx build \
  -t zephyr-dev:amd64 \
  .
