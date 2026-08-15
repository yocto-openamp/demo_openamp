# Demo RpMsg

This demo uses a zephyr app on the M7 side and some python conde on the linux side.


## Build and run

```bash
cd hmp_mcuxpresso-zephyr

./run_2_build_all.sh
sudo ./run_3_start-root.sh
```

```bash
dmsg --follow

[ 9788.823980] remoteproc remoteproc0: stopped remote processor imx-rproc
[ 9788.875421] remoteproc remoteproc0: powering up imx-rproc
[ 9788.878879] remoteproc remoteproc0: Booting fw image rpmsg_demo.elf, size 1210028
[ 9789.391001] rproc-virtio rproc-virtio.2.auto: assigned reserved memory node vdevbuffer@55400000
[ 9789.392865] virtio_rpmsg_bus virtio0: rpmsg host is online
[ 9789.393014] rproc-virtio rproc-virtio.2.auto: registered virtio0 (type 7)
[ 9789.393027] remoteproc remoteproc0: remote processor imx-rproc is now up
[ 9789.393399] virtio_rpmsg_bus virtio0: creating channel rpmsg-client-sample-py addr 0x400
```


```bash
tio --baudrate=115200 /dev/ttyUSB0

*** Booting Zephyr OS build v4.4.0-10953-gda0718ca0d52 ***
[00:00:00.004,000] <inf> rpmsg_demo: Starting Verdin iMX8MP OpenAMP RpMsg demo
[00:00:00.513,000] <inf> rpmsg_demo: Linux RPMsg endpoint is ready
[00:00:01.274,000] <inf> rpmsg_demo: RPMsg received 21 bytes: 'LINUX sending rpmsg 0'
[00:00:01.283,000] <inf> rpmsg_demo: RPMsg received 21 bytes: 'LINUX sending rpmsg 1'
[00:00:01.292,000] <inf> rpmsg_demo: RPMsg received 21 bytes: 'LINUX sending rpmsg 2'
```

```bash
ls  -1 /dev/re* /dev/rpmsg* /sys/bus/rpmsg/devices/
/dev/remoteproc0
/dev/rpmsg0
/dev/rpmsg_ctrl0

/sys/bus/rpmsg/devices/:
virtio0.rpmsg-demo-xyrx2.-1.1024
virtio0.rpmsg_ctrl.0.0
virtio0.rpmsg_ns.53.53
```

## Compare this binary against working TCM binary

```bash
export A=build/zephyr/rpmsg_demo.elf
export B=/lib/firmware/imx8mp_m7_TCM_rpmsg_lite_pingpong_rtos_linux_remote.elf
readelf -SW $A | grep resource_table
Section Headers:
  [Nr] Name              Type            Addr     Off    Size   ES Flg Lk Inf Al
  [31] .resource_table   PROGBITS        0000b680 00b798 000058 00  WA  0   0  8
readelf -SW $B | grep resource_table
Section Headers:
  [Nr] Name              Type            Addr     Off    Size   ES Flg Lk Inf Al
  [ 2] .resource_table   PROGBITS        00000400 001400 000058 00   A  0   0  1

readelf -x .resource_table $A
Hex dump of section '.resource_table':
  0x0000b680 01000000 01000000 00000000 00000000 ................
  0x0000b690 14000000 03000000 07000000 00000000 ................
  0x0000b6a0 01000000 00000000 00000000 00020000 ................
  0x0000b6b0 ffffffff 10000000 08000000 01000000 ................
  0x0000b6c0 00000000 ffffffff 10000000 08000000 ................
  0x0000b6d0 00000000 00000000                   ........

readelf -x .resource_table $B
Hex dump of section '.resource_table':
  0x00000400 01000000 01000000 00000000 00000000 ................
  0x00000410 14000000 03000000 07000000 00000000 ................
  0x00000420 01000000 00000000 00000000 00020000 ................
  0x00000430 00000055 00100000 00010000 00000000 ...U............
  0x00000440 00000000 00800055 00100000 00010000 .......U........
  0x00000450 01000000 00000000                   ........

./decode_resource_table.py $A
./decode_resource_table.py $A
```

## Fixes required to make rpmsg working

The resource table was not the fundamental fix. Standard Zephyr’s table works.

The actual fixes were:

1. **Use the shared runtime resource table** at `0x550ff000` with `CONFIG_OPENAMP_COPY_RSC_TABLE=y`, so Linux and M7 observe the same table.
2. **Map vrings through shared-memory I/O** (`shm_io_data`), after Linux resolves their addresses to:
   - vring0: `0x55000000`
   - vring1: `0x55008000`
3. **Send notifications on physical MU channel 1**, while encoding the logical vring ID in bits 16–31:
   ```c
   uint32_t message = id << 16;
   ipm_send(ipm, 0, CONFIG_OPENAMP_RSC_TABLE_IPM_TX_ID,
            &message, sizeof(message));
   ```
   This was the decisive signaling fix.
4. **Let OpenAMP allocate and free virtqueues**. Manual allocation caused ownership conflicts and a double-free fault.
5. **Increase the heap to 8192 bytes** for two 256-descriptor queues.
6. Match Linux’s expected queue configuration: **256 descriptors, 4096-byte alignment, notify IDs 0 and 1**.

In short: RPMsg started working once the shared table and vrings were mapped correctly, OpenAMP owned the queues, and M7 notified Linux using the correct MU channel and message encoding.
