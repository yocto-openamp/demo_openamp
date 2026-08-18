set -x

REPO_DIR=$(dirname "$PWD")
if [[ ! -f $REPO_DIR/PROJECT_MARKER.txt ]]; then
	echo "ERROR: Start this script from the corresponding folder!" >&2
	exit 1
fi

mkdir -p /root/firmware
echo stop > /sys/class/remoteproc/remoteproc0/state 2>/dev/null || true
echo /root/firmware > /sys/module/firmware_class/parameters/path
cp ./build/imx8mp/zephyr/demo_response_time.elf /root/firmware
echo demo_response_time.elf > /sys/class/remoteproc/remoteproc0/firmware
echo start > /sys/class/remoteproc/remoteproc0/state

