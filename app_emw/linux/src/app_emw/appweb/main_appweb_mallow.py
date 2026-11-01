from __future__ import annotations

import asyncio
import contextlib
import logging
import typing

import pydantic
import uvicorn
from experiment_datadefinitions.utils import (
    util_datasinks,
    util_datasources,
    util_pydantic,
)
from experiment_datadefinitions.utils_observer.util_message import Message, MessageVerb
from experiment_datadefinitions.utils_observer.util_observer import Observer
from fastapi import FastAPI
from nicegui import ui

from app_emw.appweb import util_webui
from app_emw.datamodel import datamodels_emw
from app_emw.lib import (
    util_app_emw,
    util_cmd_to_a53,
    util_constants,
    util_datasource_sht40,
    util_logging,
    util_observer_push,
)

logger = logging.getLogger(__name__)

util_logging.init_logging()


class HandlerCmdA53(util_cmd_to_a53.HandlerCmdA53):
    def __init__(self, observer: Observer) -> None:
        self.observer = observer

    def _notify(self, topic: str, data: pydantic.BaseModel) -> None:
        assert isinstance(topic, str)
        assert not topic.endswith("/")
        assert isinstance(data, pydantic.BaseModel)

        for field in util_pydantic.FieldInfoIter.iter_model(data):
            topic_field = f"{topic}/{field.field_name}"
            topic_value = getattr(data, field.field_name)

            if isinstance(topic_value, pydantic.BaseModel):
                self._notify(topic=topic_field, data=topic_value)
                continue

            message = Message(
                topic=topic_field,
                verb=MessageVerb.NOTIFY,
                topic_value=topic_value,
            )

            self.observer.send_message(message=message)

    @typing.override
    def handle_imu_status(self, imu_status: datamodels_emw.ModelImuStatus) -> None:
        assert isinstance(imu_status, datamodels_emw.ModelImuStatus)

        if False:
            util_cmd_to_a53.HandlerCmdA53Console.print(imu_status=imu_status)

        self._notify(
            topic=f"{util_constants.PREFIX_M7}/imu_status",
            data=imu_status,
        )

    @typing.override
    def handle_m7_status(self, m7_status: datamodels_emw.ModelM7Status) -> None:
        assert isinstance(m7_status, datamodels_emw.ModelM7Status)

        self._notify(
            topic=f"{util_constants.PREFIX_M7}/status",
            data=m7_status,
        )


class WebUIStateMallow(util_webui.WebUIState):
    def __init__(self) -> None:
        super().__init__()
        self.handler_cmd_A53 = HandlerCmdA53(observer=self.observer)


webui_state = WebUIStateMallow()


def _log_task_result(task: asyncio.Task[None]) -> None:
    if not task.cancelled() and task.exception() is not None:
        logger.error("Task %s failed", task.get_name(), exc_info=task.exception())


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI):

    await util_datasources.namedpipe_task(observer=webui_state.observer)
    util_datasinks.logger_sink(observer=webui_state.observer)

    task_app_emw = asyncio.create_task(
        util_app_emw.app_emw(
            handler_cmd_a53=webui_state.handler_cmd_A53,
            observer=webui_state.observer,
        ),
        name="app_emw",
    )
    task_app_emw.add_done_callback(_log_task_result)

    task_sht40 = asyncio.create_task(
        util_datasource_sht40.sht40_task(observer=webui_state.observer),
        name="sht40_task",
    )
    task_sht40.add_done_callback(_log_task_result)

    task_observer_push = asyncio.create_task(
        util_observer_push.observer_push_task(observer=webui_state.observer),
        name="observer_push_task",
    )
    task_observer_push.add_done_callback(_log_task_result)

    try:
        yield
    finally:
        logger.info("Done")


app = FastAPI(lifespan=lifespan)


@ui.page("/")
async def index() -> None:
    await util_webui.create_app(webui_state=webui_state)


ui.run_with(app, title="mallow-observer")


def main() -> None:
    """Start the WebUI application."""

    uvicorn.run("app_emw.appweb.main_appweb_mallow:app", reload=True)


if __name__ == "__main__":
    main()
