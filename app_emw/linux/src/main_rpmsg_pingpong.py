#!/usr/bin/env python3

import asyncio
import time

from demo_openamp.openamp.util_rpmsg import Rpmsg

# These must match the endpoint names in main.cpp.
APP_CHANNEL_NAME: str = "rpmsg-emw-APP"
IMU_CHANNEL_NAME: str = "rpmsg-emw-IMU"


async def run_pingpong(rpmsg: Rpmsg) -> None:
    count = 3

    assert rpmsg.channel is not None
    print(f"Channel {rpmsg.channel.name}")
    print(f"Created endpoint through {rpmsg.control}")
    print(f"Exchanging {count} messages through {rpmsg.endpoint}")

    received = 0
    await rpmsg.write(f"LINUX sending rpmsg {received}".encode())
    begin_s = time.monotonic()
    while received < count:
        payload = await rpmsg.read(512)
        if not payload:
            raise RuntimeError("RPMsg endpoint closed")
        received += 1
        print(f"incoming msg {received}: {payload!r}")
        if received < count:
            await rpmsg.write(f"LINUX sending rpmsg {received}".encode())

    duration_s = time.monotonic() - begin_s
    print(
        f"goodbye after {duration_s:0.1f}s! {1000.0 * duration_s / count:0.1f}ms per call."
    )


async def run_imu(rpmsg: Rpmsg) -> None:
    count = 3

    assert rpmsg.channel is not None
    print(f"Channel {rpmsg.channel.name}")
    print(f"Receiving {count} IMU samples through {rpmsg.endpoint}")

    for sample in range(1, count + 1):
        payload = await rpmsg.read(512)
        if not payload:
            raise RuntimeError("IMU RPMsg endpoint closed")
        print(f"IMU sample {sample}: {payload.decode(errors='replace')}")


def main() -> int:
    async def run() -> None:
        async with Rpmsg(
            channel_name=APP_CHANNEL_NAME, control_name=None, timeout=10.0
        ) as rpmsg_app:
            async with Rpmsg(
                channel_name=IMU_CHANNEL_NAME, control_name=None, timeout=10.0
            ) as rpmsg_imu:
                await asyncio.gather(run_pingpong(rpmsg_app), run_imu(rpmsg_imu))

    asyncio.run(run())


if __name__ == "__main__":
    main()
