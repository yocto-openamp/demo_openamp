import ctypes
import enum
import time

from app_emw.datamodel.imu_status import ModelImuStatus
from app_emw.lib.util_cmd import MsgHeader
from demo_openamp.openamp.util_rpmsg import Rpmsg
from renderer.renderer_cpp import RendererCPP


# These must match messages_to_A53.hpp.
class MSG_ID_M7_to_A53(enum.IntEnum):
    STATUS = 1
    IMU_STATUS = 2
    INTERRUPT_LINE_SENSOR = 3


async def init_cmd(rpmsg_cmd: Rpmsg) -> None:
    assert rpmsg_cmd.channel is not None
    print(f"Channel {rpmsg_cmd.channel.name}")
    print(f"Created endpoint_cmd through {rpmsg_cmd.control}")

    received = 0
    await rpmsg_cmd.write(f"LINUX sending rpmsg {received}".encode())


async def handle_cmd_pingpong(rpmsg_cmd: Rpmsg) -> None:
    count = 3
    received = 0
    print(f"Exchanging {count} messages through {rpmsg_cmd.endpoint}")

    begin_s = time.monotonic()
    while received < count:
        payload = await rpmsg_cmd.read(512)
        if not payload:
            raise RuntimeError("RPMsg endpoint closed")
        received += 1
        print(f"incoming msg {received}: {payload!r}")
        if received < count:
            await rpmsg_cmd.write(f"LINUX sending rpmsg {received}".encode())

    duration_s = time.monotonic() - begin_s
    print(
        f"goodbye after {duration_s:0.1f}s! {1000.0 * duration_s / count:0.1f}ms per call."
    )


async def handle_msg_to_A53(rpmsg_cmd: Rpmsg) -> None:
    renderer = RendererCPP(model=ModelImuStatus())
    header_size = ctypes.sizeof(MsgHeader)
    status_size = ctypes.sizeof(renderer.ctypes_model)

    while True:
        payload = await rpmsg_cmd.read(512)
        if not payload:
            raise RuntimeError("RPMsg endpoint closed")
        if len(payload) < header_size:
            raise RuntimeError(f"RPMsg payload too short for header: {len(payload)}")
        header = MsgHeader.from_buffer_copy(payload)
        if header.msg_size != len(payload):
            print(
                "WARNING:"
                f"Message size mismatch: header announces {header.msg_size},"
                f" received {len(payload)}"
            )
            continue
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
                    f" accel={status.accel_x / 1e6:+6.3f}"
                    f"/{status.accel_y / 1e6:+6.3f}"
                    f"/{status.accel_z / 1e6:+6.3f}"
                    f" gyro={status.gyro_x / 1e6:+6.3f}"
                    f"/{status.gyro_y / 1e6:+6.3f}"
                    f"/{status.gyro_z / 1e6:+6.3f}"
                )
            case _:
                raise RuntimeError(f"Unexpected message id {header.msg_id}")
