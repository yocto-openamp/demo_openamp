import asyncio
import logging
import pathlib

from experiment_datadefinitions.utils_observer import util_observer

from app_emw.lib import util_constants

logger = logging.getLogger(__name__)


async def sht40_task(observer: util_observer.Observer) -> None:

    while True:
        try:
            await asyncio.sleep(3.0)

            for address_subtopic, address_i2c in (
                ("sht40_intern", "/sys/bus/i2c/devices/3-0044/hwmon/hwmon5"),
                ("sht40_extern", "/sys/bus/i2c/devices/3-0045/hwmon/hwmon4"),
            ):
                for quantity_topic, quantity_path in (
                    ("humidity", "/humidity1_input"),
                    ("temperature", "/temp1_input"),
                ):
                    path = "/".join([address_i2c, quantity_path])
                    topic_value = int(pathlib.Path(path).read_text()) / 1000.0

                    topic = "/".join(
                        [util_constants.PREFIX_A53, address_subtopic, quantity_topic]
                    )
                    observer.send_message(
                        util_observer.Message(
                            topic=topic,
                            verb=util_observer.MessageVerb.NOTIFY,
                            topic_value=topic_value,
                        )
                    )
                    await asyncio.sleep(1.0)

        except Exception as e:
            logger.warning("sht40_task", exc_info=e)
            await asyncio.sleep(20.0)

        await asyncio.sleep(2.0)
