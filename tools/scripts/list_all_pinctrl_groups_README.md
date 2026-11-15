# list_all_pinctrl_groups

```python
app_emw/.venv/bin/python tools/scripts/list_all_pinctrl_groups.py > tools/scripts/list_all_pinctrl_groups_2026-11-15a.txt
```

# Pin Configuration Scripts

This directory contains tools to analyze the active device tree pin configurations on your i.MX8MP system.

## Scripts

### `find_alt_mode.py` - Single Group Analysis
Shows ALT mode and pin configuration for a specific pin group.

```bash
python3 find_alt_mode.py uart1grp
python3 find_alt_mode.py gpio3grp
python3 find_alt_mode.py i2c2grp
```

### `list_all_pinctrl_groups.py` - All Groups Overview
Lists all 76 pin groups with their configurations.

```bash
python3 list_all_pinctrl_groups.py
python3 list_all_pinctrl_groups.py | grep uart
python3 list_all_pinctrl_groups.py > pinctrl_dump.txt
```

Shows:
- Pin group name
- Active vs total pin pairs
- Pin reference value (hex)
- ALT mode (0-7)
- Drive strength (0-15)
- Slew rate (0-3)
- Pull-up/down configuration

### `extract_pin_mappings.py` - Generate Pin Name Mapping
Creates a mapping from pin reference values to actual pad names.

```bash
# Step 1: Download i.MX8MP pin function definitions
wget https://raw.githubusercontent.com/torvalds/linux/master/arch/arm64/boot/dts/freescale/imx8mp-pinfunc.h

# Step 2: Extract mappings
python3 extract_pin_mappings.py imx8mp-pinfunc.h > pin_mappings.txt

# Step 3: Copy output to list_all_pinctrl_groups.py PIN_REF_TO_NAME dict
```

## Understanding Pin References

The pin values shown (e.g., `0x01f8`, `0x0054`) are hex references that map to actual pad names:

- **0x0000-0x00ff**: GPIO pad references
- **0x0100-0x0fff**: Peripheral function pad references

These are defined in the i.MX8MP IOMUX controller header file.

## Data Structure

Each pin configuration contains:

```
fsl,pins = < pin_ref_1 config_1 pin_ref_2 config_2 ... >
```

Where:
- **pin_ref**: 32-bit pad reference (e.g., 0x0184)
- **config**: 32-bit configuration value with:
  - Bits 2:0 = ALT mode (ALT0-ALT7)
  - Bits 6:3 = Drive strength
  - Bits 7:6 = Slew rate
  - Bits 12:11 = Pull-up/down

## Getting Pad Names

To see actual pad names like "SAI5_RXD0" or "GPIO3_IO21":

1. **From Linux Kernel** (Recommended):
   ```bash
   # In Linux kernel source
   cat arch/arm64/boot/dts/freescale/imx8mp-pinfunc.h
   ```

2. **From i.MX8MP Datasheet**:
   - Look up the pin reference hex value in the IOMUX section
   - Maps to pad name and functions

3. **Using this helper**:
   ```bash
   python3 extract_pin_mappings.py imx8mp-pinfunc.h
   ```

## Example Interpretation

```
uart1grp:
  [0] Pad: 0x01a4 | ALT4 | Drive:4 | Slew:2 | Pull:100K_PD | Cfg:0x000001a4
```

This means:
- Pin group: uart1grp
- Pin pair index: 0
- Physical pin reference: 0x01a4 (needs mapping to PAD name)
- Alternate function: ALT4 (UART function)
- Drive strength: 4 (medium-low)
- Slew rate: 2 (medium)
- Pull resistor: 100K pull-down
- Raw config value: 0x000001a4

To find the actual pad name, look up 0x01a4 in imx8mp-pinfunc.h.

## References

- [Linux Kernel i.MX8MP Device Tree](https://github.com/torvalds/linux/tree/master/arch/arm64/boot/dts/freescale)
- [NXP i.MX8MP Datasheet](https://www.nxp.com/products/processors-and-microcontrollers/arm-processors/i-mx-applications-processors/i-mx-8-series/i-mx-8m-plus:IMX8MP)
- Linux Kernel Documentation: `Documentation/devicetree/bindings/pinctrl/fsl,imx8mp-pinctrl.txt`
