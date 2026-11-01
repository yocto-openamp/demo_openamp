from __future__ import annotations

from experiment_datadefinitions.utils import util_pydantic
from experiment_datadefinitions.utils_observer.util_message import Message, MessageVerb
from experiment_datadefinitions.utils_observer.util_observer import (
    Observer,
    Registration,
)
from experiment_datadefinitions.webui.widgets import simple_editors
from nicegui import ui

from app_emw.datamodel import datamodels_emw


class WebUIState:
    def __init__(self) -> None:
        self.observer = Observer()
        self.model = datamodels_emw.ModelEMW()

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
                    for f in self.hierarchy.all_elements
                ]
            )

        self.observer.register_as_observer(
            registration=Registration(
                topic="/",
                callback=observer_callback,
            )
        )


async def create_app(webui_state: WebUIState) -> None:
    """PID Controller Web UI"""

    # with ui.column().classes("w-full max-w-2xl gap-0 p-4"):
    def dump_elements(mh: util_pydantic.ModelHierarchy) -> None:
        assert isinstance(mh, util_pydantic.ModelHierarchy)

        for _hierarchy in mh.compounds.values():
            with ui.expansion(_hierarchy.title, value=True).classes("w-full"):
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
