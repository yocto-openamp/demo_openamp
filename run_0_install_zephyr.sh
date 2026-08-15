set -euox pipefail

if [[ ! -f ./PROJECT_MARKER.txt ]]; then
	echo "ERROR: Start this script from the corresponding folder!" >&2
	exit 1
fi

ZEPHYR_SDK_INSTALL_DIR="${ZEPHYR_SDK_INSTALL_DIR:-$HOME/zephyr-sdk-1.0.1}"
export ZEPHYR_SDK_INSTALL_DIR

time (
    rm -rf .venv .west build bootloader modules zephyr

    uv venv --python 3.13.13
    . .venv/bin/activate

    uv pip install west

    west init . --manifest-url https://github.com/zephyrproject-rtos/zephyr --manifest-rev v4.4.2 --clone-opt=--depth=1


    export WEST_NUCLEO="hal_stm32 cmsis_6"
    export WEST_IMX="hal_nxp open-amp libmetal"
    west update zephyr $WEST_NUCLEO $WEST_IMX

    uv pip install -r zephyr/scripts/requirements-base.txt

    west sdk install \
    --install-dir "$ZEPHYR_SDK_INSTALL_DIR" \
    --gnu-toolchains arm-zephyr-eabi
)