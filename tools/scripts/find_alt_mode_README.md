
```bash
app_emw/.venv/bin/python tools/scripts/find_alt_mode.py uart1grp

uart1grp - Pin Configuration:
  Pin #0: ALT4, Drive:4, Slew:2, Pull:100K_PD (0x000001a4)
  Pin #1: ALT4, Drive:0, Slew:0, Pull:100K_PD (0x00000404)
  Pin #2: ALT4, Drive:12, Slew:3, Pull:100K_PD (0x000005e4)
  Pin #3: ALT4, Drive:0, Slew:0, Pull:100K_PD (0x00000004)
  Pin #4: ALT2, Drive:0, Slew:0, Pull:100K_PD (0x00000002)
  Pin #5: ALT4, Drive:8, Slew:3, Pull:100K_PD (0x000001c4)
  Pin #6: ALT0, Drive:5, Slew:2, Pull:100K_PD (0x000001a8)
  Pin #7: ALT0, Drive:1, Slew:0, Pull:100K_PD (0x00000408)
  Pin #9: ALT4, Drive:0, Slew:0, Pull:100K_PD (0x00000004)
  Pin #11: ALT4, Drive:8, Slew:3, Pull:100K_PD (0x000001c4)
  Pin #12: ALT0, Drive:4, Slew:0, Pull:100K_PD (0x00000220)
  Pin #13: ALT0, Drive:0, Slew:2, Pull:100K_PD (0x00000480)
  Pin #14: ALT0, Drive:13, Slew:3, Pull:100K_PD (0x000005e8)
  Pin #16: ALT4, Drive:0, Slew:0, Pull:100K_PD (0x00000004)
  Pin #17: ALT4, Drive:8, Slew:3, Pull:100K_PD (0x000001c4)
  Pin #18: ALT4, Drive:4, Slew:0, Pull:100K_PD (0x00000224)
  Pin #19: ALT4, Drive:0, Slew:2, Pull:100K_PD (0x00000484)
  Pin #23: ALT4, Drive:8, Slew:3, Pull:100K_PD (0x000001c4)
```

```bash
app_emw/.venv/bin/python tools/scripts/find_alt_mode.py i2c2grp


i2c2grp - Pin Configuration:
  Pin #0: ALT0, Drive:1, Slew:0, Pull:100K_PD (0x00000208)
  Pin #1: ALT0, Drive:13, Slew:1, Pull:100K_PD (0x00000468)
  Pin #2: ALT4, Drive:5, Slew:2, Pull:100K_PD (0x000005ac)
  Pin #4: ALT2, Drive:0, Slew:0, Pull:100K_PD (0x00000002)
  Pin #5: ALT6, Drive:8, Slew:3, Pull:100K_PD (0x400001c6)
  Pin #6: ALT4, Drive:1, Slew:0, Pull:100K_PD (0x0000020c)
  Pin #7: ALT4, Drive:13, Slew:1, Pull:100K_PD (0x0000046c)
  Pin #8: ALT0, Drive:6, Slew:2, Pull:100K_PD (0x000005b0)
  Pin #10: ALT2, Drive:0, Slew:0, Pull:100K_PD (0x00000002)
  Pin #11: ALT6, Drive:8, Slew:3, Pull:100K_PD (0x400001c6)
```

```bash
app_emw/.venv/bin/python tools/scripts/find_alt_mode.py gpio3grp

gpio3grp - Pin Configuration:
  Pin #0: ALT0, Drive:5, Slew:0, Pull:100K_PD (0x00000028)
  Pin #1: ALT0, Drive:1, Slew:2, Pull:100K_PD (0x00000288)
  Pin #5: ALT4, Drive:0, Slew:2, Pull:100K_PD (0x00000184)
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