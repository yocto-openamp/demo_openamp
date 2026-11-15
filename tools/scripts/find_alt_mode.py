#!/usr/bin/env python3
"""
Extract ALT mode and other pin configuration from i.MX IOMUX device tree.

i.MX IOMUX Configuration Value Format (32-bit):
    Bits 2:0    = ALT mode (ALT0-ALT7) - which peripheral function is assigned
    Bits 6:3    = Drive strength (0-15, higher = stronger drive)
    Bits 7:6    = Slew rate (0-3, controls rise/fall time)
    Bits 12:11  = Pull-up/down configuration (00=PD, 01=PD, 10=PU, 11=PU)
    Bits 15:13  = Reserved/Additional configuration
    Bits 31:16  = (when reading from device tree, context-dependent)

Example: 0x000001a4 = ALT4 with drive strength 5, slew rate 2
         0x400001c6 = ALT6 with pull-up and drive strength 8
"""
import struct
import sys


def decode_config(config_val):
    """Decode all fields from i.MX IOMUX configuration value."""
    alt_mode = config_val & 0x7  # bits 2:0
    drive_strength = (config_val >> 3) & 0xF  # bits 6:3
    slew_rate = (config_val >> 6) & 0x3  # bits 7:6
    pull_config = (config_val >> 11) & 0x3  # bits 12:11

    pull_labels = {0: "100K_PD", 1: "47K_PD", 2: "100K_PU", 3: "22K_PU"}

    return {
        "alt": alt_mode,
        "drive": drive_strength,
        "slew": slew_rate,
        "pull": pull_labels.get(pull_config, "unknown"),
    }


# Read pin configuration from device tree
group_name = sys.argv[1] if len(sys.argv) > 1 else "uart1grp"
path = f"/sys/firmware/devicetree/base/soc@0/bus@30000000/pinctrl@30330000/{group_name}/fsl,pins"

with open(path, "rb") as f:
    data = f.read()

print(f"\n{group_name} - Pin Configuration:")
print(f"Total pins in group: {len(data) // 4}")
for i in range(0, len(data), 4):
    val = struct.unpack(">I", data[i : i + 4])[0]
    pin_idx = i // 4
    if val != 0:
        cfg = decode_config(val)
        print(
            f"  Pin #{pin_idx}: ALT{cfg['alt']}, "
            f"Drive:{cfg['drive']}, Slew:{cfg['slew']}, "
            f"Pull:{cfg['pull']} (0x{val:08x})"
        )
    else:
        print(f"  Pin #{pin_idx}: (empty/unused)")
