set -x

modprobe rpmsg_ns
modprobe rpmsg_ctrl
modprobe rpmsg_char
# modprobe -r imx_rpmsg_tty 2>/dev/null || true
# modprobe -r rpmsg-client-sample 2>/dev/null || true

mkdir -p /root/firmware
echo stop > /sys/class/remoteproc/remoteproc0/state 2>/dev/null || true
echo /root/firmware > /sys/module/firmware_class/parameters/path
cp ./build/zephyr/rpmsg_demo.elf /root/firmware
echo rpmsg_demo.elf > /sys/class/remoteproc/remoteproc0/firmware
echo start > /sys/class/remoteproc/remoteproc0/state

python3 python/src/openamp/main_rpmsg_pingpong.py