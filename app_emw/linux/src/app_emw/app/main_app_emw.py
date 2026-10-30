import asyncio
import ctypes
import pathlib
import time

from app_emw.datamodel.imu_status import ModelImuStatus
from app_emw.lib.util_constants import IMU_MEASUREMENTS_FILE
from app_emw.lib.util_imu_file import IMU_MEASUREMENT_SIZE
from app_emw.lib.util_messages import MsgHeader
from app_emw.lib.util_messages_to_A53 import MSG_ID_M7_to_A53
from app_emw.lib.util_messages_to_M7 import RPMSG_IMU_START
from demo_openamp.openamp.util_rpmsg import Rpmsg
from renderer.renderer_cpp import RendererCPP

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


async def run_imu(rpmsg: Rpmsg, output_file: pathlib.Path) -> None:
    # The firmware sends one gyro measurement after every 10 accel measurements.
    count = 100

    assert rpmsg.channel is not None
    print(f"Channel {rpmsg.channel.name}")
    print(f"Receiving {count} IMU measurements through {rpmsg.endpoint}")

    # The first Linux message lets OpenAMP learn this endpoint's return address.
    await rpmsg.write(RPMSG_IMU_START)

    with output_file.open("wb") as file:
        for _ in range(count):
            payload = await rpmsg.read(512)
            if not payload:
                raise RuntimeError("IMU RPMsg endpoint closed")
            if len(payload) != IMU_MEASUREMENT_SIZE:
                raise RuntimeError(f"Unexpected IMU payload size {len(payload)}")
            file.write(payload)

    print(f"Wrote {count} IMU measurements to {output_file}")


async def handle_msg_to_A53(rpmsg: Rpmsg) -> None:
    renderer = RendererCPP(model=ModelImuStatus())
    header_size = ctypes.sizeof(MsgHeader)
    status_size = ctypes.sizeof(renderer.ctypes_model)

    while True:
        payload = await rpmsg.read(512)
        if not payload:
            raise RuntimeError("RPMsg endpoint closed")
        if len(payload) < header_size:
            raise RuntimeError(f"RPMsg payload too short for header: {len(payload)}")
        header = MsgHeader.from_buffer_copy(payload)
        if header.msg_size != len(payload):
            raise RuntimeError(
                f"Message size mismatch: header announces {header.msg_size},"
                f" received {len(payload)}"
            )
        match header.msg_id:
            case MSG_ID_M7_to_A53.IMU_STATUS:
                if len(payload) != header_size + status_size:
                    raise RuntimeError(f"Unexpected IMU status size {len(payload)}")

                status = renderer.deserialize_from_cpp(payload[header_size:])
                assert isinstance(status, ModelImuStatus)

                # Accel values are in m/s^2, gyro values in rad/s.
                print(
                    f"IMU status: count={status.measurement_count}"
                    f" errors={status.measurement_count_error}"
                    f" accel {status.accel_x / 1e6:0.3f}"
                    f"/{status.accel_y / 1e6:0.3f}"
                    f"/{status.accel_z / 1e6:0.3f}"
                    f" gyro {status.gyro_x / 1e6:0.3f}"
                    f"/{status.gyro_y / 1e6:0.3f}"
                    f"/{status.gyro_z / 1e6:0.3f}"
                )
            case _:
                raise RuntimeError(f"Unexpected message id {header.msg_id}")


def main() -> int:
    async def run() -> None:
        async with (
            Rpmsg(
                channel_name=APP_CHANNEL_NAME, control_name=None, timeout=10.0
            ) as rpmsg_app,
            Rpmsg(
                channel_name=IMU_CHANNEL_NAME, control_name=None, timeout=10.0
            ) as rpmsg_imu,
        ):
            # IMU status shares this channel, so finish the ping-pong first.
            await run_pingpong(rpmsg_app)
            await asyncio.gather(
                handle_msg_to_A53(rpmsg_app),
                run_imu(rpmsg_imu, IMU_MEASUREMENTS_FILE),
            )

    asyncio.run(run())


if __name__ == "__main__":
    main()
