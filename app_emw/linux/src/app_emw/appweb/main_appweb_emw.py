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
from experiment_datadefinitions.utils_observer.util_observer import (
    Observer,
    Registration,
)
from experiment_datadefinitions.webui.widgets import simple_editors
from fastapi import FastAPI
from nicegui import ui

from app_emw.datamodel import datamodels_emw
from app_emw.lib import (
    util_app_emw,
    util_cmd_to_a53,
    util_constants,
    util_datasource_sht40,
    util_logging,
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
            topic_value = getattr(data, field.field_name)

            message = Message(
                topic=f"{topic}/{field.field_name}",
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


class WebUIState:
    def __init__(self) -> None:
        self.observer = Observer()
        self.model = datamodels_emw.ModelEMW()
        self.handler_cmd_A53 = HandlerCmdA53(observer=self.observer)

        self.hierarchy = util_pydantic.ModelHierarchy.factory(
            model=self.model,
            prefix="/",
        )
        for element in self.hierarchy.all_elements:
            self.observer.send_message(
                Message(
                    topic=element.topic,
                    verb=MessageVerb.REGISTER,
                    topic_value=element.value,
                ),
            )

        self.hierarchy_text = "...change a value and the hierarchy will appear here..."

        def observer_callback(message: Message) -> None:
            self.hierarchy_text = "\n".join(
                [
                    f"{f.topic} {repr(f.value)} ({message.verb.name})"
                    for f in webui_state.hierarchy.all_elements
                ]
            )

        self.observer.register_as_observer(
            registration=Registration(
                topic="/",
                callback=observer_callback,
            )
        )


webui_state = WebUIState()


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

    try:
        yield
    finally:
        logger.info("Done")


app = FastAPI(lifespan=lifespan)


async def create_app() -> None:
    """PID Controller Web UI"""

    # with ui.column().classes("w-full max-w-2xl gap-0 p-4"):
    def dump_elements(mh: util_pydantic.ModelHierarchy) -> None:
        assert isinstance(mh, util_pydantic.ModelHierarchy)

        for _topic, _hierarchy in mh.compounds.items():
            with ui.expansion(_hierarchy.title, value=True).classes("w-full"):
                # logger.debug(f"compound: {topic} - {item.model!r}")
                dump_elements(mh=_hierarchy)

        for topic, item in mh.elements.items():
            # logger.debug(f"element:  {topic} - {item.value_type_name}")
            try:
                f_create_field = simple_editors.TYPE_MAP_NICE_GUI[item.value_type]
            except KeyError:
                ui.label(
                    f"{item.field_name}: unsupported field type {item.value_type_name}"
                )
                continue

            with ui.row().classes("w-full items-center gap-0 p-0 pl-4"):
                f_create_field(observer=webui_state.observer, topic=topic, field=item)  # type: ignore[call-arg]

    dump_elements(mh=webui_state.hierarchy)


@ui.page("/")
async def index() -> None:
    await create_app()


ui.run_with(app, title="EMW Web UI")


def main() -> None:
    """Start the WebUI application."""

    uvicorn.run("app_emw.appweb.main_appweb_emw:app", reload=True)


if __name__ == "__main__":
    main()
