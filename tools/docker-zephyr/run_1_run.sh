set -euox pipefail

docker run --rm -it \
    -v "$PWD:/workspace" \
    zephyr-dev:$(uname -m)
