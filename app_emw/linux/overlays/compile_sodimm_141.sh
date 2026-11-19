#!/bin/bash
# SODIMM_141 GPIO Overlay - Quick Start Script
# This script automates the compilation and installation of the GPIO overlay

set -e

OVERLAY_DIR="/var/rootdirs/home/torizon/demo_openamp/app_emw/linux/overlays"
BOOT_DIR="/boot"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║      SODIMM_141 GPIO Overlay - Compilation & Installation    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Compile
echo "STEP 1: Compiling device tree overlay..."
cd "$OVERLAY_DIR"
dtc -@ -I dts -O dtb -o sodimm_141_gpio.dtbo sodimm_141_gpio.dts
echo "✓ Compiled: sodimm_141_gpio.dtbo"
echo ""

# Step 2: Install
echo "STEP 2: Installing overlay to /boot..."
sudo cp sodimm_141_gpio.dtbo "$BOOT_DIR/"
echo "✓ Installed to: $BOOT_DIR/sodimm_141_gpio.dtbo"
echo ""

# Step 3: Enable
echo "STEP 3: Enabling overlay at boot time..."
echo "Command to run:"
echo "  sudo fw_setenv fdt_overlays verdin-imx8mp_hmp_overlay.dtbo sodimm_141_gpio.dtbo"
echo ""
echo "After running above, reboot with:"
echo "  sudo reboot"
echo ""

# Step 4: Verification info
echo "STEP 4: After reboot, verify with:"
echo "  gpioinfo gpiochip1 | grep sodimm_141"
echo ""
echo "STEP 5: Control GPIO:"
echo "  Set HIGH:  sudo gpioset gpiochip1 7=1"
echo "  Set LOW:   sudo gpioset gpiochip1 7=0"
echo "  Toggle:    sudo gpioset --toggle=1000 gpiochip1 7=1"
echo ""

echo "═════════════════════════════════════════════════════════════════"
echo "✓ Overlay compilation complete!"
echo "═════════════════════════════════════════════════════════════════"
