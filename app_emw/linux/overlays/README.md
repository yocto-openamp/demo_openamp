# GPIO Overlays for Verdin iMX8MP

This directory contains device tree overlays to configure SODIMM pins as GPIO outputs.

## SODIMM_135 GPIO Overlay

This overlay configures **SODIMM_135** (GPIO4_IO23) as a GPIO output.

### Compilation

```bash
dtc -@ -I dts -O dtb -o sodimm_135_gpio.dtbo sodimm_135_gpio.dts
```

### Installation & Enabling

```bash
sudo cp sodimm_135_gpio.dtbo /boot/
sudo fw_setenv fdt_overlays verdin-imx8mp_hmp_overlay.dtbo sodimm_135_gpio.dtbo
sudo reboot
```

### Usage

```bash
# Set to high (1)
sudo gpioset gpiochip3 23=1

# Set to low (0)
sudo gpioset gpiochip3 23=0

# Toggle with 1 second interval
sudo gpioset --toggle=1000 gpiochip3 23=1
```

### Verification

```bash
gpioinfo gpiochip3 | grep sodimm_135
```

---

## SODIMM_141 GPIO Overlay

This overlay configures **SODIMM_141** (GPIO2_IO7, formerly UART2_RTS) as a GPIO output.

### Pin Information

- **SODIMM Pin:** 141
- **SoC Pad Name:** SD1_DATA5
- **GPIO Reference:** GPIO2_IO7
- **GPIO Number:** 71
- **X19 Header Pin:** 23 (on Mallow carrier board)
- **Default Function:** USDHC1_DATA5 (SD/eMMC card data)
- **ALT Mode:** ALT5 (for GPIO function)

### Compilation

```bash
dtc -@ -I dts -O dtb -o sodimm_141_gpio.dtbo sodimm_141_gpio.dts
```

### Installation & Enabling

```bash
sudo cp sodimm_141_gpio.dtbo /boot/
sudo fw_setenv fdt_overlays verdin-imx8mp_hmp_overlay.dtbo sodimm_141_gpio.dtbo
sudo reboot
```

### Usage

After reboot, control the GPIO with `gpioset`:

```bash
# Set to high (1)
sudo gpioset gpiochip1 7=1

# Set to low (0)
sudo gpioset gpiochip1 7=0

# Toggle with 1 second interval
sudo gpioset --toggle=1000 gpiochip1 7=1
```

### Verification

Check if the GPIO is available:

```bash
gpioinfo gpiochip1 | grep sodimm_141
```

### ⚠️ Important Notes

- **SD/eMMC Access:** Enabling this overlay disables SD/eMMC card functionality on that pin. Only use this if you don't need USDHC1 on SD1_DATA5.
- **UART2 Flow Control:** This pin would normally be used for UART2_RTS flow control. Only reconfigure if UART2 flow control is not needed.
- **GPIO Chip:** GPIO2_IO7 is on gpiochip1 (not gpiochip2), which is why commands use `gpiochip1`.

---

## References

For detailed pin mapping information, see: `../../SODIMM_141_ANALYSIS.md`

### Datasheets

- **Verdin i.MX8MP:** https://docs.toradex.com/116795-verdin_imx8mp_datasheet.pdf
- **Mallow Carrier Board:** https://docs.toradex.com/113873-mallow-carrier-board-datasheet.pdf
