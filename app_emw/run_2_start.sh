set -x

REPO_DIR=$(dirname "$PWD")
if [[ ! -f $REPO_DIR/PROJECT_MARKER.txt ]]; then
	echo "ERROR: Start this script from the corresponding folder!" >&2
	exit 1
fi

modprobe rpmsg_ns
modprobe rpmsg_ctrl
modprobe rpmsg_char
# modprobe -r imx_rpmsg_tty 2>/dev/null || true
# modprobe -r rpmsg-client-sample 2>/dev/null || true

mkdir -p /home/torizon/firmware
echo stop > /sys/class/remoteproc/remoteproc0/state 2>/dev/null || true
echo /home/torizon/firmware > /sys/module/firmware_class/parameters/path
cp ./build/zephyr/demo_rpmsg.elf /home/torizon/firmware
echo demo_rpmsg.elf > /sys/class/remoteproc/remoteproc0/firmware
echo start > /sys/class/remoteproc/remoteproc0/state

$REPO_DIR/.venv/bin/python linux/src/main_rpmsg_pingpong.py
