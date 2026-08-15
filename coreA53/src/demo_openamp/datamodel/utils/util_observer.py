from __future__ import annotations

import asyncio
import dataclasses
import enum
import logging
import random
import typing

logger = logging.getLogger(__file__)


class EnumItemQuality(enum.StrEnum):
    UNKNOWN = "unknown"
    KNOWN = "known"
    IN_TRANSITION = "intransition"


@dataclasses.dataclass(slots=True)
class ObservableItem:
    path: str
    value: typing.Any
    quality: EnumItemQuality

    @property
    def quality_text(self) -> str:
        return self.quality.value


class Observer:
    def __init__(self) -> None:
        self.items: dict[str, ObservableItem] = {}
        self.observer_callbacks: list[typing.Callable] = []
        self.notify_active = 0

    def register_observer_callback(
        self,
        callback: typing.Callable[[str, str], None],
    ) -> None:
        self.observer_callbacks.append(callback)

    def register_with_value(self, path: str, value: typing.Any) -> None:
        print(f"register_with_value({path}, {value}")
        if path in self.items:
            logger.error(f"Already registered in observer: {path}")
            return
        self.items[path] = ObservableItem(
            path=path,
            value=value,
            quality=EnumItemQuality.UNKNOWN,
        )

    def get_item(self, path: str) -> ObservableItem:
        item = self.items.get(path)
        assert item is not None
        return item

    async def set_quality_known(self, quality_int: int) -> None:
        quality = EnumItemQuality.KNOWN if quality_int else EnumItemQuality.UNKNOWN
        items = list(self.items.values())
        random.shuffle(items)
        for item in items:
            item.quality = quality
            await asyncio.sleep(0.2)

    async def set_request(self, path: str, value: typing.Any) -> typing.Any:
        """
        Returns the value which has been set.
        """
        logger.info(f"set_request({path}, {value})")
        item = self.get_item(path=path)
        # .value = value
        item.quality = EnumItemQuality.IN_TRANSITION
        self.notify_active += 1
        try:
            await asyncio.sleep(2)
        finally:
            self.notify_active -= 1
        if self.notify_active > 0:
            # Avoid cycling
            return
        self.notify(path=path, value=value)
        return value

    def notify(self, path: str, value: typing.Any) -> None:
        logger.info(f"notify({path}, {value})")
        self.notify_active += 1
        try:
            item = self.get_item(path=path)
            if item.value != value:
                item.value = value
            item.quality = EnumItemQuality.KNOWN

            for callback in self.observer_callbacks:
                try:
                    callback(path=path, value=value)
                except Exception as e:
                    logger.exception(msg="callback failed", exc_info=e)
        finally:
            self.notify_active -= 1
