set -euox pipefail

dockerdocker run --rm -it \
    -v "$PWD:/workspace" \
    zephyr-dev
