# App EMW

## Goal

Configure the app to communicate with the ICM-45686 over SPI on the Verdin i.MX8MP.
Use the pin mapping below.
The code should be minimal just to prove that SPI communication works, say the PCB is correct.

The given app has to be enhanced to

* Read a ICM-45686
* SPI_1_CLK:  X19-1, SODIMM_196
* SPI_1_MISO: X19-2, SODIMM_198
* SPI_1_MOSI: X19-3, SODIMM_200
* SPI_1_CS:   X19-4, SODIMM_202

As a first step:
* app_emw/zephyr/prj_verdin_imx8mp.overlay: Add ICM-45686
* app_emw/zephyr/src/main.cpp: In main(): Add a loop which reads every second a measurement and prints it to the console.


## Tools

You are on the board with a connected ICM-45686. You may compile here and run the application!

**Build application**

```bash
run_1_build_full.sh
```

If only C++ code changed:

```bash
run_1_build_incr.sh
```

**Run application**

```bash
run_2_start.sh
```

View/log the output

```bash
stty -F /dev/ttymxc1 115200 raw -echo
cat /dev/ttymxc1 | tee uart_dump.bin
```
