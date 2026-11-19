# find_alt_mode.py

Decodes i.MX8MP pinctrl groups from the running device tree (`/sys/firmware/devicetree/base/.../pinctrl@30330000`).
Each `fsl,pins` entry is 6 cells: mux_reg, conf_reg, input_reg, mux_mode (ALT), input_val, pad_conf.
This is what the DT *requests*; the kernel's applied state is in `/sys/kernel/debug/pinctrl/30330000.pinctrl/pinmux-pins` (root).

```bash
app_emw/.venv/bin/python tools/scripts/find_alt_mode.py uart1grp

uart1grp - 4 pin(s):
  [ 0] MX8MP_IOMUXC_SAI2_RXD0__UART1_DCE_RTS        ALT4  mux:0x1a4 input:0x5e4=2  pad:0x000001c4 (DSE:X2 SLOW PULL-UP SCHMITT)
  [ 1] MX8MP_IOMUXC_SAI2_TXFS__UART1_DCE_CTS        ALT4  mux:0x1a8  pad:0x000001c4 (DSE:X2 SLOW PULL-UP SCHMITT)
  [ 2] MX8MP_IOMUXC_UART1_RXD__UART1_DCE_RX         ALT0  mux:0x220 input:0x5e8=4  pad:0x000001c4 (DSE:X2 SLOW PULL-UP SCHMITT)
  [ 3] MX8MP_IOMUXC_UART1_TXD__UART1_DCE_TX         ALT0  mux:0x224  pad:0x000001c4 (DSE:X2 SLOW PULL-UP SCHMITT)
```

```bash
app_emw/.venv/bin/python tools/scripts/find_alt_mode.py i2c2grp

i2c2grp - 2 pin(s):
  [ 0] MX8MP_IOMUXC_I2C2_SCL__I2C2_SCL              ALT0  mux:0x208 input:0x5ac=2  pad:0x400001c6 (DSE:X6 SLOW PULL-UP SCHMITT SION)
  [ 1] MX8MP_IOMUXC_I2C2_SDA__I2C2_SDA              ALT0  mux:0x20c input:0x5b0=2  pad:0x400001c6 (DSE:X6 SLOW PULL-UP SCHMITT SION)
```

```bash
app_emw/.venv/bin/python tools/scripts/find_alt_mode.py gpio3grp

gpio3grp - 1 pin(s):
  [ 0] MX8MP_IOMUXC_GPIO1_IO05__GPIO1_IO05          ALT0  mux:0x028  pad:0x00000184 (DSE:X2 SLOW PULL-DOWN SCHMITT)
```

```bash
app_emw/.venv/bin/python tools/scripts/find_alt_mode.py --pad SD1_DATA4
Groups using pad SD1_DATA4 (mux:0x0a4):

sodimm_143_gpio_pins: MALFORMED - 5 cells, not a multiple of 6 (missing pad config?): 0xa4 0x304 0x0 0x5 0x0

uart2ctsgrp - 1 pin(s):
  [ 0] MX8MP_IOMUXC_SD1_DATA4__UART2_DCE_RTS        ALT4  mux:0x0a4 input:0x5ec=0  pad:0x000001c4 (DSE:X2 SLOW PULL-UP SCHMITT)
```

Example:

| X19 | SODIMM pin | Ball Name | GPIO | error |
| - | - | - | - | - |
| 17 | 129 | UART1_RXD | GPIO5_IO22 | |
| 18 | 131 | UART1_TXD | GPIO5_IO23 | |
| 19 | 133 | UART1_CTS | GPIO4_IO24 | mallow datasheets: RTS |
| 20 | 135 | UART1_RTS | GPIO4_IO23 | mallow datasheets: CTS |
| 21 | 137 | UART2_RXD | GPIO5_IO24 | |
| 22 | 139 | UART2_TXD | GPIO5_IO25 | |
| 23 | 141 | UART2_CTS | GPIO2_IO7 | mallow datasheets: RTS |
| 24 | 143 | UART2_RTS | GPIO2_IO6 | mallow datasheets: CTS |

X19-19 -> GPIO4_IO24 -> gpio3grp, pin 