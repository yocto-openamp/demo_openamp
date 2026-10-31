import io
import logging
import pathlib

from demo_openamp.openamp.util_rpmsg import Rpmsg
from experiment_datadefinitions.utils_observer import util_message, util_observer

from app_emw.lib.util_cmd_to_m7 import RPMSG_IMU_START
from app_emw.lib.util_imu_file import IMU_MEASUREMENT_SIZE

logger = logging.getLogger(__name__)


async def init_imu(rpmsg_imu: Rpmsg) -> None:
    assert rpmsg_imu.channel is not None
    print(f"Channel {rpmsg_imu.channel.name}")

    # The first Linux message lets OpenAMP learn this endpoint's return address.
    await rpmsg_imu.write(RPMSG_IMU_START)


class FiledumpImu:
    _TOPIC = "/a53/common/log_imu"

    def __init__(
        self,
        observer: util_observer.Observer | None,
        output_file: pathlib.Path,
    ) -> None:
        self.output_file = output_file
        self.output_f: io.BufferedWriter | None = None
        if observer is None:
            return

        output_file.unlink(missing_ok=True)

        observer.register_as_observer(
            registration=util_observer.Registration(
                topic=self._TOPIC,
                callback=self._observer_callback,
            )
        )

    def _observer_callback(self, message: util_message.Message) -> None:
        if message.topic != self._TOPIC:
            return

        logger.info(
            f"{message.verb.name}({message.topic}, {message.topic_value}): Logging to: {self.output_file}"
        )

        if self.output_f is not None:
            self.output_f.close()
            self.output_f = None

        if message.topic_value:
            assert self.output_f is None
            self.output_f = self.output_file.open("wb")
            return

    async def handle_measurements_imu(self, rpmsg_imu: Rpmsg) -> None:
        while True:
            payload = await rpmsg_imu.read(512)
            if not payload:
                raise RuntimeError("IMU RPMsg endpoint closed")
            if len(payload) != IMU_MEASUREMENT_SIZE:
                raise RuntimeError(f"Unexpected IMU payload size {len(payload)}")

            if self.output_f is not None:
                self.output_f.write(payload)
