#!/usr/bin/env python3
"""
Helper script to extract i.MX8MP IOMUX pin definitions from imx8mp-pinfunc.h
and create a PIN_REF_TO_NAME mapping.

Usage:
    # Auto-download/cache to extract_pin_mappings.py_imx8mp-pinfunc.h:
    python3 extract_pin_mappings.py

    # Or use local file:
    python3 extract_pin_mappings.py /path/to/imx8mp-pinfunc.h

The script will:
1. Check if extract_pin_mappings.py_imx8mp-pinfunc.h exists (cached)
2. If not, download from Linux kernel GitHub and cache it
3. Extract and generate PIN_REF_TO_NAME dictionary
"""

import pathlib
import re
import sys
import urllib.request
from io import StringIO

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
FILENAME_PINFUC_H = DIRECTORY_OF_THIS_FILE / "extract_pin_mappings_tmp_imx8mp-pinfunc.h"
FILENAME_MAPPINGS = DIRECTORY_OF_THIS_FILE / "extract_pin_mappings_tmp_mappings.py"


def download_pinfunc_header(cache_path: pathlib.Path) -> str:
    """Download imx8mp-pinfunc.h from Linux kernel GitHub and cache it"""
    url = "https://raw.githubusercontent.com/torvalds/linux/master/arch/arm64/boot/dts/freescale/imx8mp-pinfunc.h"
    print(f"Downloading {url}...", file=sys.stderr)
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            content = response.read().decode("utf-8")
        # Save to cache
        with open(cache_path, "w") as f:
            f.write(content)
        print(f"Cached to {cache_path}", file=sys.stderr)
        return content
    except Exception as e:
        print(f"Error downloading file: {e}", file=sys.stderr)
        sys.exit(1)


def extract_mappings(pinfunc_file: pathlib.Path) -> dict[int, str]:
    """Extract pin reference to name mappings from imx8mp-pinfunc.h"""
    mappings = {}

    # Try cache first, otherwise download
    if pinfunc_file.exists():
        content = pinfunc_file.read_text()
        print(f"Using cached file: {pinfunc_file}", file=sys.stderr)
    else:
        content = download_pinfunc_header(pinfunc_file)

    # Pattern: #define MX8MP_IOMUXC_PAD__FUNCTION 0xXXXX
    # Example: #define MX8MP_IOMUXC_SAI5_RXD0__GPIO3_IO21 0x0184
    pattern = r"#define\s+(MX8MP_IOMUXC_\S+)\s+(0x[0-9A-Fa-f]+)"

    for match in re.finditer(pattern, content):
        macro_name = match.group(1)
        hex_value = int(match.group(2), 16)
        mappings[hex_value] = macro_name

    return mappings


def generate_python_dict(mappings: dict[int, str]) -> str:
    """Generate Python dictionary code for PIN_REF_TO_NAME"""
    output = StringIO()
    output.write("PIN_REF_TO_NAME = {\n")
    for hex_val in sorted(mappings.keys()):
        name = mappings[hex_val]
        output.write(f'    0x{hex_val:04x}: "{name}",\n')
    output.write("}\n")
    return output.getvalue()


if __name__ == "__main__":
    pinfunc_file = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else FILENAME_PINFUC_H

    mappings = extract_mappings(pinfunc_file)

    # Generate output
    dict_output = generate_python_dict(mappings)

    # Write to file
    FILENAME_MAPPINGS.write_text(dict_output)

    print(f"Output saved to: {FILENAME_MAPPINGS.name}", file=sys.stderr)
