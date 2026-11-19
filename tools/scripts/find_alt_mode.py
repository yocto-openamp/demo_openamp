#!/usr/bin/env python3
"""
Decode i.MX8MP pinctrl groups from the running Linux device tree.

Each entry in a group's ``fsl,pins`` property is 6 big-endian u32 cells:

    mux_reg  conf_reg  input_reg  mux_mode  input_val  pad_conf

    mux_reg    offset of IOMUXC_SW_MUX_CTL_PAD_<pad>   (identifies the pad)
    conf_reg   offset of IOMUXC_SW_PAD_CTL_PAD_<pad>
    input_reg  offset of the daisy-chain SELECT_INPUT register (0 = none)
    mux_mode   bits 2:0 = ALT mode, bit 4 = SION
    input_val  value written to input_reg
    pad_conf   pad control value (bits per imx8mp-pinfunc.h):
                 bits 2:1 DSE   (0x0 X1, 0x4 X2, 0x2 X4, 0x6 X6)
                 bit 4    FSEL  (fast slew)
                 bit 5    ODE   (open drain)
                 bit 6    PUE   (1 = pull-up, 0 = pull-down)
                 bit 7    HYS   (Schmitt trigger)
                 bit 8    PE    (pull enable)
                 bit 30   SION  (DT-only flag, moved into mux_mode by Linux)
                 bit 31   NO_PAD_CTL (DT-only flag, pad register left untouched)

The macro name (e.g. MX8MP_IOMUXC_SD1_DATA4__UART2_DCE_RTS) is looked up in
imx8mp-pinfunc.h by (mux_reg, mux_mode, input_reg).

This shows what the device tree *requests*. What the kernel actually applied
is in /sys/kernel/debug/pinctrl/30330000.pinctrl/pinmux-pins (needs root).

Usage:
    find_alt_mode.py <group> [<group> ...]   decode the given groups
    find_alt_mode.py --pad SD1_DATA4         every group that uses this pad
    find_alt_mode.py --all                   decode all groups
"""

import argparse
import pathlib
import re
import struct
import sys

PINCTRL = pathlib.Path("/sys/firmware/devicetree/base/soc@0/bus@30000000/pinctrl@30330000")
PINFUNC_H = pathlib.Path(__file__).with_name("extract_pin_mappings_tmp_imx8mp-pinfunc.h")

CELLS_PER_PIN = 6
DSE = {0x0: "X1", 0x4: "X2", 0x2: "X4", 0x6: "X6"}
RE_DEFINE = re.compile(r"#define\s+(MX8MP_IOMUXC_(\w+?)__\w+)\s+(0x[0-9A-Fa-f]+)\s+(0x[0-9A-Fa-f]+)\s+(0x[0-9A-Fa-f]+)\s+(0x[0-9A-Fa-f]+)\s+(0x[0-9A-Fa-f]+)")


def load_pinfunc() -> tuple[dict, dict]:
    """Return ({(mux_reg, mode, input_reg): macro}, {mux_reg: pad_name})."""
    functions: dict[tuple[int, int, int], str] = {}
    pads: dict[int, str] = {}
    if not PINFUNC_H.is_file():
        return functions, pads
    for line in PINFUNC_H.read_text().splitlines():
        m = RE_DEFINE.match(line)
        if not m:
            continue
        macro, pad = m.group(1), m.group(2)
        mux_reg, _conf, input_reg, mode, _ival = (int(x, 16) for x in m.groups()[2:])
        functions.setdefault((mux_reg, mode, input_reg), macro)
        pads.setdefault(mux_reg, pad)
    return functions, pads


def decode_pad_conf(val: int) -> str:
    if val & 0x80000000:
        return "NO_PAD_CTL"
    parts = [f"DSE:{DSE[val & 0x6]}", "FAST" if val & 0x10 else "SLOW"]
    if val & 0x100:
        parts.append("PULL-UP" if val & 0x40 else "PULL-DOWN")
    else:
        parts.append("NO-PULL")
    if val & 0x80:
        parts.append("SCHMITT")
    if val & 0x20:
        parts.append("OPEN-DRAIN")
    if val & 0x40000000:
        parts.append("SION")
    return " ".join(parts)


def read_cells(group: str) -> tuple[int, ...] | None:
    path = PINCTRL / group / "fsl,pins"
    if not path.is_file():
        return None
    data = path.read_bytes()
    return struct.unpack(f">{len(data) // 4}I", data)


def decode_entry(cells: tuple[int, ...], functions: dict, pads: dict) -> str:
    mux_reg, _conf_reg, input_reg, mux_mode, input_val, pad_conf = cells
    alt = mux_mode & 0x7
    sion = " SION" if mux_mode & 0x10 else ""
    name = functions.get((mux_reg, alt, input_reg))
    if name is None:
        name = f"{pads.get(mux_reg, f'mux@0x{mux_reg:03x}')} (function unknown)"
    daisy = f" input:0x{input_reg:03x}={input_val}" if input_reg else ""
    return (
        f"{name:<44} ALT{alt}{sion}  mux:0x{mux_reg:03x}{daisy}  "
        f"pad:0x{pad_conf:08x} ({decode_pad_conf(pad_conf)})"
    )


def print_group(group: str, functions: dict, pads: dict, only_mux: int | None = None) -> bool:
    cells = read_cells(group)
    if cells is None:
        print(f"{group}: no fsl,pins property under {PINCTRL}", file=sys.stderr)
        return False
    if len(cells) % CELLS_PER_PIN:
        # e.g. an overlay that used a pinfunc macro but forgot the pad value
        if only_mux is None or only_mux in cells[::CELLS_PER_PIN]:
            print(f"\n{group}: MALFORMED - {len(cells)} cells, not a multiple of {CELLS_PER_PIN} "
                  f"(missing pad config?): {' '.join(f'0x{c:x}' for c in cells)}")
        return False
    entries = [cells[i : i + CELLS_PER_PIN] for i in range(0, len(cells), CELLS_PER_PIN)]
    if only_mux is not None:
        entries = [e for e in entries if e[0] == only_mux]
        if not entries:
            return True
    print(f"\n{group} - {len(cells) // CELLS_PER_PIN} pin(s):")
    for i, entry in enumerate(cells[j : j + CELLS_PER_PIN] for j in range(0, len(cells), CELLS_PER_PIN)):
        if entry in entries:
            print(f"  [{i:2}] {decode_entry(entry, functions, pads)}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("groups", nargs="*", help="pinctrl group name(s), e.g. uart2ctsgrp")
    parser.add_argument("--pad", help="list all groups using this pad, e.g. SD1_DATA4")
    parser.add_argument("--all", action="store_true", help="decode every group")
    args = parser.parse_args()

    functions, pads = load_pinfunc()
    all_groups = sorted(p.parent.name for p in PINCTRL.glob("*/fsl,pins"))

    if args.pad:
        wanted = args.pad.upper().removeprefix("MX8MP_IOMUXC_")
        mux = next((reg for reg, name in pads.items() if name == wanted), None)
        if mux is None:
            print(f"Unknown pad '{args.pad}' (not found in {PINFUNC_H.name})", file=sys.stderr)
            return 1
        print(f"Groups using pad {wanted} (mux:0x{mux:03x}):")
        for group in all_groups:
            print_group(group, functions, pads, only_mux=mux)
        return 0

    groups = all_groups if args.all else (args.groups or ["uart1grp"])
    ok = [print_group(g, functions, pads) for g in groups]
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
