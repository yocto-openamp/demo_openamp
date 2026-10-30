# App EMW

This demo uses a zephyr app on the M7 side and some python conde on the linux side.

## Prepare uv

```bash
cd linux
uv venv
. .venv/bin/activate
uv sync --all-extras
```

## Build and run

```bash
./run_1_build_full.sh
./run_2_start.sh
```


```bash
tio --baudrate=115200 /dev/ttyUSB0 # External UART
tio --baudrate=115200 /dev/ttymxc1 # Internal UART loopback

# or
stty -F /dev/ttymxc1 115200 raw -echo
cat /dev/ttymxc1 | tee /tmp/app_emw-uart.log

*** Booting Zephyr OS build 4.4.99 ***
[00:00:00.003,000] <inf> app_emw: Starting Verdin iMX8MP OpenAMP RpMsg demo
[00:00:00.516,000] <inf> app_emw: Linux RPMsg endpoint is ready
[00:00:00.960,000] <inf> app_emw: RPMsg received 21 bytes: 'LINUX sending rpmsg 0'
[00:00:00.968,000] <inf> app_emw: RPMsg received 21 bytes: 'LINUX sending rpmsg 1'
[00:00:00.976,000] <inf> app_emw: RPMsg received 21 bytes: 'LINUX sending rpmsg 2'
```
