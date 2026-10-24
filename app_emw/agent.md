# App EMW: ICM-45686 SPI Bring-Up

## Objective

Make the Verdin i.MX8MP M7 application communicate with the connected
ICM-45686 over SPI. Keep the implementation focused on a simple hardware
bring-up test.

The sensor is wired as follows:

| SPI signal | Verdin connector | SoM pin |
|---|---|---|
| SPI_1_CLK | X19-1 | SODIMM_196 |
| SPI_1_MISO | X19-2 | SODIMM_198 |
| SPI_1_MOSI | X19-3 | SODIMM_200 |
| SPI_1_CS | X19-4 | SODIMM_202 |

## First milestone

1. Review the existing Zephyr board configuration and use its established
   device-tree and driver conventions.
2. In `zephyr/prj_verdin_imx8mp.overlay`, configure the SPI controller for the
   listed connections and add the ICM-45686 device.
3. In `zephyr/src/main.cpp`, read the accelerometer X, Y, and Z values once per
   second through Zephyr's sensor API and print the named values in m/s^2.
   Report sensor initialization or read errors explicitly; never print
   placeholder data as a successful reading.
4. Build and run on the connected board. Success means repeated valid readings
   appear on the console without sensor communication errors. No particular
   values are expected while the board is stationary.

## Build and run

Run commands from the `app_emw/` directory on the board:

```bash
./run_1_build_full.sh
```

After a successful full build, use the incremental build when only C++ source
has changed:

```bash
./run_1_build_incr.sh
```

Start the application with:

```bash
./run_2_start.sh
```

## View console output

On the Linux side of the board, configure the internal UART and capture output
in a separate terminal:

```bash
stty -F /dev/ttymxc1 115200 raw -echo
cat /dev/ttymxc1 | tee /tmp/app_emw-uart.log
```

Stop the capture with Ctrl+C. Check that the repeated accelerometer readings
are present and that no sensor initialization or read errors were logged.