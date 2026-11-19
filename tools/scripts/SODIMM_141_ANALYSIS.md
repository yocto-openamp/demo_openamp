# SODIMM_141 (UART_2_RTS) Pin Configuration Analysis

## ⚠️ IMPORTANT FINDING

**SODIMM_141 is NOT currently configured for UART2_RTS in the running Linux system!**

---

## Current Status in Running Linux System

The actual device tree loaded on this system shows:

```
Device Tree: /sys/firmware/devicetree/base/soc@0/bus@30000000/pinctrl@30330000/uart2rtsgrp/

uart2rtsgrp Pin #1:
  Pad Name: SD1_DATA5 (GPIO2_IO7)
  Configuration Value: 0x00000308
  ALT Mode: ALT0 (not ALT4!)
  Function: USDHC1_DATA5 (SD/eMMC Card Data Line)
  Drive Strength: 1
  Slew Rate: 0
  Pull-up/down: 100K_PD
```

**This means:**
- SODIMM_141 / SD1_DATA5 is currently allocated for SD/eMMC card operation
- It is **NOT** configured for UART2 flow control
- To enable UART2_RTS, the ALT mode would need to be changed from **ALT0 → ALT4**

---

## Path from Verdin Datasheet Table 17 to SODIMM_141

### Step-by-Step Mapping:

**1️⃣ Start: Verdin i.MX8MP Datasheet - Table 17: SoC Pins Mapping**
   - Lists all iMX8MP SoC balls/pads and their available alternate functions

**2️⃣ Locate Physical Pad: SD1_DATA5**
   - Official ball/pad name on the i.MX8MP SoC
   - Found in Table 17 under the IOMUX/mux section

**3️⃣ Check IOMUX Offset: 0x0A8**
   - Register offset within IOMUXC controller (base address: 0x30330000)
   - Full register address: 0x30330000 + 0x0A8 = 0x303300A8

**4️⃣ Examine Available Alternate Functions from pinfunc.h**
   
   SD1_DATA5 can be configured as:
   
   | ALT Mode | Function | Use Case |
   |----------|----------|----------|
   | ALT0 | USDHC1_DATA5 | SD/eMMC card data line #5 ← **CURRENT** |
   | ALT1 | ENET1_TX_ER | Ethernet transmission error |
   | ALT3 | I2C1_SDA | I2C1 serial data line |
   | ALT4 | UART2_DTE_RTS | UART2 flow control (RTS) ← **NEEDED FOR UART2_RTS** |
   | ALT5 | GPIO2_IO7 | General Purpose I/O |

**5️⃣ GPIO Reference: GPIO2_IO7**
   - Available when configured as ALT5 (GPIO mode)
   - GPIO Number: (Port 2 × 32) + Pin 7 = GPIO #71
   - Currently not in use (pin is in ALT0 mode)

**6️⃣ Physical SODIMM Connector: Pin 141**
   - Verdin i.MX8MP datasheet maps the SD1_DATA5 signal → SODIMM connector pin 141
   - This is the physical signal path on the Verdin SoM module

**7️⃣ Mallow Carrier Board Mapping: Table 21 - X19 Header**
   - X19 (Primary Extension Header) Pin 23 connects to SODIMM 141
   - Mallow labels this as: **UART2_RTS** (flow control signal)
   - Note: Verdin datasheet labels it as UART2_CTS (reverse naming)

**8️⃣ Current Configuration in Linux Device Tree**
   - Actual file: `/sys/firmware/devicetree/base/soc@0/bus@30000000/pinctrl@30330000/`
   - Device tree group: `uart2rtsgrp`
   - Pin #1 shows: ALT0, **not** ALT4

---

## Configuration Comparison

### Current Configuration (ALT0 - USDHC1)
```
Configuration Value: 0x00000308
ALT Mode: ALT0
Function: USDHC1_DATA5
Drive Strength: 1
Slew Rate: 0
Pull: 100K_PD
Purpose: SD/eMMC card operation
```

### Required Configuration for UART2_RTS (ALT4)
```
Configuration Value: 0x000001c4
ALT Mode: ALT4
Function: UART2_DTE_RTS
Drive Strength: 8
Slew Rate: 3
Pull: 100K_PD
Purpose: UART2 flow control signal
```

---

## Complete Mapping Chain

```
Verdin i.MX8MP SoC    Verdin SODIMM      Mallow X19          Current Function
   Pad/Ball           Connector Pin      Header Pin          (this system)
   ──────────         ──────────────     ──────────────      ──────────────────
   SD1_DATA5   ───→   SODIMM 141   ───→  X19-23      ───→  USDHC1_DATA5 (ALT0)
   (Offset 0xA8)      (GPIO2_IO7)        (SODIMM_141)         [Not UART2_RTS!]
   
   
   To enable UART2_RTS:
                                                             UART2_RTS (ALT4)
                                                             [Requires reconfiguration]
```

---

## Configuration Summary Table

| Property | Current Value | For UART2_RTS |
|----------|-------|-------|
| **SoC Pad Name** | SD1_DATA5 | (same) |
| **GPIO Reference** | GPIO2_IO7 | (same) |
| **GPIO Number** | 71 | (same) |
| **IOMUX Offset** | 0x0A8 | (same) |
| **IOMUX Register** | 0x303300A8 | (same) |
| **SODIMM Pin** | 141 | (same) |
| **X19 Header Pin** | 23 | (same) |
| **Mallow Label** | UART2_RTS | (same) |
| **Verdin Label** | UART2_CTS | (same) |
| **Current ALT Mode** | **ALT0** | **ALT4** (required) |
| **Current Function** | **USDHC1_DATA5** | **UART2_DTE_RTS** |
| **Config Value** | 0x00000308 | 0x000001c4 |
| **Drive Strength** | 1 | 8 |
| **Slew Rate** | 0 | 3 |
| **Device Tree Path** | /sys/firmware/devicetree/base/.../uart2rtsgrp | (would need overlay) |

---

## How to Enable UART2_RTS on SODIMM_141

To use SODIMM_141 as UART2_RTS, you would need to:

1. **Create a device tree overlay** (similar to `app_emw/linux/overlays/sodimm_135_gpio.dts`)
2. **Change the configuration** from ALT0 (USDHC1) to ALT4 (UART2_RTS)
3. **Understand the trade-off:** This would disable SD/eMMC card functionality for that pin

Example overlay structure:
```devicetree
/dts-v1/;
/plugin/;

/ {
  fragment@0 {
    target = <&iomuxc>;
    __overlay__ {
      uart2_rts_sd1_data5 {
        fsl,pins = < MX8MP_IOMUXC_SD1_DATA5__UART2_DTE_RTS 0x1c4 >;
      };
    };
  };
};
```

---

## Alternative Configurations

The same physical pad (SD1_DATA5) can be used for different purposes:

- **ALT0:** USDHC1_DATA5 (SD/eMMC) - **CURRENT**
- **ALT1:** ENET1_TX_ER (Ethernet)
- **ALT3:** I2C1_SDA (I2C bus)
- **ALT4:** UART2_DTE_RTS (UART2 flow control)
- **ALT5:** GPIO2_IO7 (GPIO control - accessible as /sys/class/gpio/gpio71/)

---

## Supporting Information

### Pin Function Definitions from imx8mp-pinfunc.h

```c
// All possible configurations for SD1_DATA5 (offset 0x0A8)
#define MX8MP_IOMUXC_SD1_DATA5__USDHC1_DATA5    0x0A8 0x308 0x000 0x0 0x0
#define MX8MP_IOMUXC_SD1_DATA5__ENET1_TX_ER     0x0A8 0x308 0x000 0x1 0x0
#define MX8MP_IOMUXC_SD1_DATA5__I2C1_SDA        0x0A8 0x308 0x5A8 0x3 0x0
#define MX8MP_IOMUXC_SD1_DATA5__UART2_DCE_CTS   0x0A8 0x308 0x000 0x4 0x0
#define MX8MP_IOMUXC_SD1_DATA5__UART2_DTE_RTS   0x0A8 0x308 0x5EC 0x4 0x1
#define MX8MP_IOMUXC_SD1_DATA5__GPIO2_IO07      0x0A8 0x308 0x000 0x5 0x0
```

Format: `PIN_REF | OFFSET | SELECT_INPUT | ALT_MODE | VARIANT`

### Scripts Used

- **`find_alt_mode.py`** - Reads actual device tree configuration from running system
- **`list_all_pinctrl_groups.py`** - Lists all pin groups and their settings
- **`extract_pin_mappings.py`** - Extracts pin definitions from kernel header

### Device Tree Loaded

```
System: imx8mp-verdin-nonwifi-mallow
Path: /boot/ostree/torizon-*/dtb/imx8mp-verdin-nonwifi-mallow.dtb
Type: Compiled Binary Device Tree (.dtb)
```

---

## References

1. **Verdin i.MX8MP Datasheet**
   - Table 17: SoC Pins Mapping (Continued)
   - https://docs.toradex.com/116795-verdin_imx8mp_datasheet.pdf

2. **Mallow Carrier Board Datasheet**
   - Table 21: Primary Extension Header (X19) (Continued)
   - https://docs.toradex.com/113873-mallow-carrier-board-datasheet.pdf

3. **Linux Kernel Device Tree Source**
   - File: `arch/arm64/boot/dts/freescale/imx8mp-pinfunc.h`
   - Repository: https://github.com/torvalds/linux

4. **NXP i.MX8MP Reference Manual**
   - IOMUX Controller specifications

---

**Document Generated:** 2026-11-19  
**Analysis Scope:** SODIMM_141 (UART_2_RTS) Pin Configuration  
**Status:** Currently ALT0 (USDHC1_DATA5) - NOT configured as UART2_RTS  
**Analysis Method:** Actual Linux device tree interrogation via /sys/firmware/devicetree/base/
