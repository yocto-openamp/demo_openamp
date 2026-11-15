# SODIMM_135 GPIO Overlay

This overlay configures **SODIMM_135** (GPIO4_IO23) as a GPIO output for the Verdin iMX8MP.

## Compilation

Compile the device tree overlay:

```bash
dtc -@ -I dts -O dtb -o sodimm_135_gpio.dtbo sodimm_135_gpio.dts
```

## Installation

Copy the compiled overlay to the boot partition:

```bash
sudo cp sodimm_135_gpio.dtbo /boot/
```

## Enabling the overlay

Add the overlay to your device tree boot configuration:

```bash
sudo fw_setenv fdt_overlays verdin-imx8mp_hmp_overlay.dtbo sodimm_135_gpio.dtbo
sudo reboot
```

## Usage

After reboot, control the GPIO with `gpioset`:

```bash
# Set to high (1)
sudo gpioset gpiochip3 23=1

# Set to low (0)
sudo gpioset gpiochip3 23=0

# Toggle with 1 second interval
sudo gpioset --toggle=1000 gpiochip3 23=1
```

## Verification

Check if the GPIO is available:

```bash
gpioinfo gpiochip3 | grep sodimm_135
```
