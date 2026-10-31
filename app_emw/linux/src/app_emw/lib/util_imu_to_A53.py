import pathlib

from app_emw.lib.util_cmd_to_M7 import RPMSG_IMU_START
from app_emw.lib.util_imu_file import IMU_MEASUREMENT_SIZE
from demo_openamp.openamp.util_rpmsg import Rpmsg


async def init_imu(rpmsg_imu: Rpmsg) -> None:
    assert rpmsg_imu.channel is not None
    print(f"Channel {rpmsg_imu.channel.name}")

    # The first Linux message lets OpenAMP learn this endpoint's return address.
    await rpmsg_imu.write(RPMSG_IMU_START)


async def handle_measurements_imu(rpmsg_imu: Rpmsg, output_file: pathlib.Path) -> None:
    # The firmware sends one gyro measurement after every 10 accel measurements.
    count = 100
    print(f"Receiving {count} IMU measurements through {rpmsg_imu.endpoint}")

    with output_file.open("wb") as file:
        for _ in range(count):
            payload = await rpmsg_imu.read(512)
            if not payload:
                raise RuntimeError("IMU RPMsg endpoint closed")
            if len(payload) != IMU_MEASUREMENT_SIZE:
                raise RuntimeError(f"Unexpected IMU payload size {len(payload)}")
            file.write(payload)

    print(f"Wrote {count} IMU measurements to {output_file}")
