import asyncio

from demo_openamp.openamp.util_rpmsg import Rpmsg
from experiment_datadefinitions.utils_observer import util_observer

from app_emw.lib import util_cmd_to_a53, util_constants, util_imu_file, util_imu_to_a53


async def app_emw(
    handler_cmd_a53: util_cmd_to_a53.HandlerCmdA53,
    observer: util_observer.Observer | None = None,
) -> None:
    """
    The EMW application just handling the rpmsg signals.
    Without GUI, observer, etc!
    """
    filenump_imu = util_imu_to_a53.FiledumpImu(
        output_file=util_imu_file.IMU_MEASUREMENTS_FILE,
        observer=observer,
    )

    async with (
        Rpmsg(
            channel_name=util_constants.CHANNEL_NAME_CMD,
            control_name=None,
            timeout=10.0,
        ) as rpmsg_cmd,
        Rpmsg(
            channel_name=util_constants.CHANNEL_NAME_IMU,
            control_name=None,
            timeout=10.0,
        ) as rpmsg_imu,
    ):
        # IMU status shares this channel, so finish the ping-pong first.
        await util_cmd_to_a53.init_cmd(rpmsg_cmd=rpmsg_cmd)
        await util_imu_to_a53.init_imu(rpmsg_imu=rpmsg_imu)
        await util_cmd_to_a53.handle_cmd_pingpong(rpmsg_cmd=rpmsg_cmd)
        await asyncio.gather(
            handler_cmd_a53.handle_msg_to_A53(rpmsg_cmd=rpmsg_cmd),
            filenump_imu.handle_measurements_imu(rpmsg_imu=rpmsg_imu),
        )
