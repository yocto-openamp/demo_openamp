from __future__ import annotations

import contextlib
import logging

import uvicorn
from app_emw.datamodel.imu_status import ModelEMW
from app_emw.lib import util_constants, util_logging
from fastapi import FastAPI
from nicegui import ui
from utils import (
    util_datasinks,
    util_datasources,
    util_pydantic,
)
from utils_observer.util_message import Message, MessageVerb
from utils_observer.util_observer import Observer, Registration
from webui.widgets import simple_editors

logger = logging.getLogger(__name__)

util_logging.init_logging()


class WebUIState:
    def __init__(self) -> None:
        self.observer = Observer()
        self.model = ModelEMW()
        self.hierarchy = util_pydantic.ModelHierarchy.factory(
            model=self.model,
            prefix=f"{util_constants.PREFIX_M7}",
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


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI):
    await util_datasources.namedpipe_task(observer=webui_state.observer)
    util_datasinks.logger_sink(observer=webui_state.observer)
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

    def dump(mh: util_pydantic.ModelHierarchy) -> None:
        assert isinstance(mh, util_pydantic.ModelHierarchy)

        use_tabs = False
        if use_tabs:
            # Tabs
            dict_tabs = {}

            with ui.tabs().classes("w-full") as tabs:
                for topic, item in mh.compounds.items():
                    # dict_tabs[path] = ui.tab(f"{path}: {item.title}")
                    dict_tabs[topic] = ui.tab(item.title)

                dict_tabs["/custom"] = ui.tab("customized")

            with ui.tab_panels(tabs).classes("w-full"):
                for topic, item in mh.compounds.items():
                    current_tab = dict_tabs[topic]
                    with ui.tab_panel(current_tab).classes("w-full"):
                        print(f"compount: {topic} - {item.model!r}")
                        dump_elements(mh=item)

                current_tab = dict_tabs["/custom"]
                with ui.tab_panel(current_tab).classes("w-full"):
                    ui.label("Customized")

        else:
            # Expansion
            for _topic, item in mh.compounds.items():
                with ui.expansion(item.title, value=True).classes("w-full"):
                    # logger.debug(f"compound: {topic} - {item.model!r}")
                    dump_elements(mh=item)

            if False:
                with ui.expansion("Custom", value=True).classes("w-full"):
                    with ui.row().classes("w-full items-center gap-0 p-0 pl-4"):
                        topic = f"{PREFIX_M7}/common/debuglevel"
                        simple_editors.create_selection_field(
                            options={
                                0: "off",
                                1: "debug",
                                2: "info",
                                3: "warn",
                                4: "error",
                            },
                            observer=webui_state.observer,
                            topic=topic,
                            field=mh.get_by_topic(topic).field,
                        )

                    with ui.row().classes("w-full items-center gap-0 p-0 pl-4"):
                        topic = f"{PREFIX_M7}/axis_x/value"
                        simple_editors.create_slider_field(
                            observer=webui_state.observer,
                            topic=topic,
                            field=mh.get_by_topic(topic).field,
                        )

                    with ui.row().classes("w-full items-center gap-0 p-0 pl-4"):
                        ui.code().bind_content_from(webui_state, "hierarchy_text")

    dump(mh=webui_state.hierarchy)


@ui.page("/")
async def index() -> None:
    await create_app()


ui.run_with(app, title="EMW Web UI")


def main() -> None:
    """Start the WebUI application."""

    uvicorn.run("app_emw.appweb.main_appweb_emw:app", reload=True)


if __name__ == "__main__":
    main()
