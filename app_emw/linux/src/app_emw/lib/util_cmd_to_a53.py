import abc
import ctypes
import enum
import time
import typing

from demo_openamp.openamp.util_rpmsg import Rpmsg
from experiment_datadefinitions.renderer.renderer_cpp import RendererCPP

from app_emw.datamodel import datamodels_emw
from app_emw.lib.util_cmd import MsgHeader


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


class HandlerCmdA53(abc.ABC):
    """
    Async method which dispatches messages to
    methods which must be overridden.
    """

    _HEADER_SIZE = ctypes.sizeof(MsgHeader)

    async def handle_msg_to_A53(self, rpmsg_cmd: Rpmsg) -> None:

        while True:
            payload_rpmsg = await rpmsg_cmd.read(512)
            if not payload_rpmsg:
                raise RuntimeError("RPMsg endpoint closed")
            if len(payload_rpmsg) < self._HEADER_SIZE:
                raise RuntimeError(
                    f"RPMsg payload too short for header: {len(payload_rpmsg)}"
                )
            header = MsgHeader.from_buffer_copy(payload_rpmsg)
            if header.msg_size != len(payload_rpmsg):
                print(
                    "WARNING:"
                    f"Message size mismatch: header announces {header.msg_size},"
                    f" received {len(payload_rpmsg)}"
                )
                continue

            self._handle_msg(header=header, payload_rpmsg=payload_rpmsg)

    def _handle_msg(self, header: MsgHeader, payload_rpmsg: bytes) -> None:
        assert isinstance(header, MsgHeader)
        assert isinstance(payload_rpmsg, bytes)

        payload_cmd = payload_rpmsg[self._HEADER_SIZE :]

        match header.msg_id:
            case MSG_ID_M7_to_A53.IMU_STATUS:
                renderer = RendererCPP(model=datamodels_emw.ModelImuStatus())
                status_size = ctypes.sizeof(renderer.ctypes_model)
                if len(payload_cmd) != status_size:
                    raise RuntimeError(f"Unexpected IMU status size {len(payload_cmd)}")

                imu_status = renderer.deserialize_from_cpp(payload_cmd)
                assert isinstance(imu_status, datamodels_emw.ModelImuStatus)

                self.handle_imu_status(imu_status=imu_status)

            case MSG_ID_M7_to_A53.STATUS:
                # This must match msg_m7_status_t in main.cpp.
                renderer = RendererCPP(model=datamodels_emw.ModelM7StatusChannel())
                channel_size = ctypes.sizeof(renderer.ctypes_model)
                if len(payload_cmd) != 2 * channel_size:
                    raise RuntimeError(f"Unexpected M7 status size {len(payload_cmd)}")

                channel_cmd = renderer.deserialize_from_cpp(payload_cmd[:channel_size])
                channel_imu = renderer.deserialize_from_cpp(payload_cmd[channel_size:])
                assert isinstance(channel_cmd, datamodels_emw.ModelM7StatusChannel)
                assert isinstance(channel_imu, datamodels_emw.ModelM7StatusChannel)

                self.handle_m7_status(
                    m7_status=datamodels_emw.ModelM7Status(
                        channel_cmd=channel_cmd,
                        channel_imu=channel_imu,
                    )
                )
            case _:
                raise RuntimeError(f"Unexpected message id {header.msg_id}")

    @abc.abstractmethod
    def handle_imu_status(self, imu_status: datamodels_emw.ModelImuStatus) -> None: ...

    @abc.abstractmethod
    def handle_m7_status(self, m7_status: datamodels_emw.ModelM7Status) -> None: ...


class HandlerCmdA53Console(HandlerCmdA53):
    @typing.override
    def handle_imu_status(self, imu_status: datamodels_emw.ModelImuStatus) -> None:
        self.print(imu_status=imu_status)

    @typing.override
    def handle_m7_status(self, m7_status: datamodels_emw.ModelM7Status) -> None:
        assert isinstance(m7_status, datamodels_emw.ModelM7Status)
        for name, channel in (
            ("CMD", m7_status.channel_cmd),
            ("IMU", m7_status.channel_imu),
        ):
            print(
                f"M7 channel {name}: tx_ok={channel.tx_ok}"
                f" tx_err={channel.tx_err}"
                f" tx_last_err={channel.tx_last_err}"
                f" rx_ok={channel.rx_ok}"
            )

    @staticmethod
    def print(imu_status: datamodels_emw.ModelImuStatus) -> None:
        assert isinstance(imu_status, datamodels_emw.ModelImuStatus)
        # Accel values are in m/s^2, gyro values in rad/s.
        print(
            f"IMU status: count={imu_status.measurement_count}"
            f" errors={imu_status.measurement_count_error}"
            f" accel={imu_status.accel_x:+6.3f}"
            f"/{imu_status.accel_y:+6.3f}"
            f"/{imu_status.accel_z:+6.3f}"
            f" gyro={imu_status.gyro_x:+6.3f}"
            f"/{imu_status.gyro_y:+6.3f}"
            f"/{imu_status.gyro_z:+6.3f}"
        )
