# 

USER_LED_1_RED → SODIMM 52 → i.MX 8M Plus GPIO3_IO00
USER_LED_1_GREEN → SODIMM 54 → GPIO3_IO01
USER_LED_2_RED → SODIMM 56 → GPIO3_IO06
USER_LED_2_GREEN → SODIMM 58 → GPIO3_IO07

https://git.toradex.com/cgit/linux-toradex.git/tree/arch/arm64/boot/dts/freescale/imx8mp-verdin-mallow.dtsi

sudo fw_setenv fdtfile imx8mp-verdin-nonwifi-mallow.dtb
sudo fw_setenv fdt_overlays verdin-imx8mp_hmp_overlay.dtbo
sudo reboot

tr '\0' '\n' < /proc/device-tree/model

echo 1 > /sys/class/leds/red:debug-1/brightness
echo 1 > /sys/class/leds/red:debug-2/brightness
echo 1 > /sys/class/leds/green:debug-1/brightness
echo 1 > /sys/class/leds/green:debug-2/brightness
