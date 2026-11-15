#!/usr/bin/env python3
"""
List all pinctrl groups and their pin configurations from the active device tree.

Automatically discovers all pin groups under the IOMUX controller and displays
their configurations including ALT mode, drive strength, slew rate, and pull-up/down.

To find the actual pad names (ball names), you need the i.MX8MP IOMUX definitions:
- Linux Kernel: arch/arm64/boot/dts/freescale/imx8mp-pinfunc.h
- NXP BSP: Look in your bootloader or kernel device tree sources
- The pin_ref values here (0x28, 0x1a4, etc.) map to MX8MP_IOMUXC_PAD_* macros
"""

import pathlib
import struct

from extract_pin_mappings_tmp_mappings import PIN_REF_TO_NAME

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
FILENAME_OUT = DIRECTORY_OF_THIS_FILE / "list_all_pinctrl_groups_tmp_out.txt"


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


def get_all_groups(pinctrl_base):
    """Find all pin group directories."""
    groups = []
    try:
        for item in pathlib.Path(pinctrl_base).iterdir():
            if item.is_dir() and item.name.endswith("grp"):
                groups.append(item.name)
    except FileNotFoundError:
        print(f"Error: pinctrl controller not found at {pinctrl_base}")
        return []

    return sorted(groups)


def display_group_config(f, group_name, pinctrl_base):
    """Display configuration for a single group."""
    pins_file = pathlib.Path(pinctrl_base) / group_name / "fsl,pins"

    try:
        data = pins_file.read_bytes()
    except FileNotFoundError:
        print("  (fsl,pins not found)", file=f)
        return

    # Parse as pairs: (pin_ref, config)
    pairs = []
    for i in range(0, len(data), 8):
        pin_ref = struct.unpack(">I", data[i : i + 4])[0]
        config = struct.unpack(">I", data[i + 4 : i + 8])[0] if i + 4 < len(data) else 0
        pairs.append((pin_ref, config))

    active_pairs = sum(1 for pin_ref, cfg in pairs if pin_ref != 0 or cfg != 0)

    print(f"\n{group_name} ({active_pairs}/{len(pairs)} pairs active):", file=f)

    for pair_idx, (pin_ref, config) in enumerate(pairs):
        if pin_ref == 0 and config == 0:
            continue

        cfg = decode_config(config)
        pad_name = PIN_REF_TO_NAME.get(pin_ref, f"0x{pin_ref:04x}")

        print(
            f"  [{pair_idx:2d}] Pad: {pad_name:40s} | ALT{cfg['alt']} | "
            f"Drive:{cfg['drive']:2d} | Slew:{cfg['slew']} | "
            f"Pull:{cfg['pull']:8s} | Cfg:0x{config:08x}",
            file=f,
        )


def main():
    pinctrl_base = pathlib.Path(
        "/sys/firmware/devicetree/base/soc@0/bus@30000000/pinctrl@30330000"
    )

    if not pinctrl_base.exists():
        print(f"Error: Device tree not found at {pinctrl_base}")
        return

    groups = get_all_groups(pinctrl_base)

    if not groups:
        print("No pin groups found")
        return

    with FILENAME_OUT.open("w") as f:
        print(f"Found {len(groups)} pin groups in iomuxc controller", file=f)
        print("\nNote: Pin pad names require i.MX8MP IOMUX definitions from:", file=f)
        print(
            "  - Linux kernel: arch/arm64/boot/dts/freescale/imx8mp-pinfunc.h", file=f
        )
        print("\n" + "=" * 100, file=f)

        for group in groups:
            display_group_config(f, group, pinctrl_base)

        print("\n" + "=" * 100, file=f)
        print(f"Total groups: {len(groups)}", file=f)
        print(
            "\nTo find pad names (ball names), look up the pin references in:", file=f
        )
        print(
            "  i.MX8MP datasheet or kernel: arch/arm64/boot/dts/freescale/imx8mp-pinfunc.h",
            file=f,
        )

    print(f"Wrote: {FILENAME_OUT}")


if __name__ == "__main__":
    main()
