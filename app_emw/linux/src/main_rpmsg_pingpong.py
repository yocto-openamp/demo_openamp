#!/usr/bin/env python3

import asyncio
import time

from demo_openamp.openamp.util_rpmsg import Rpmsg

# This must match with the same string in main.cpp
CHANNEL_NAME: str = "rpmsg-demo-xyrx2"


async def run_pingpong() -> None:
    count = 3

    async with Rpmsg(
        channel_name=CHANNEL_NAME, control_name=None, timeout=10.0
    ) as rpmsg:
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


def main() -> int:
    asyncio.run(run_pingpong())


if __name__ == "__main__":
    main()
