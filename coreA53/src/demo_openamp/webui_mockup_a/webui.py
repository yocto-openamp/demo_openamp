from __future__ import annotations

import contextlib
import logging

import uvicorn
from fastapi import FastAPI
from nicegui import ui

from ..datamodel.utils import util_logging

logger = logging.getLogger(__file__)

util_logging.init_logging()

# ui.colors(primary="#6e93d6")
# ui.colors(primary="#d66ed2", secondary="#a4d66e", dark="#003cff")


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        yield
    finally:
        logger.info("Done")


app = FastAPI(lifespan=lifespan)


async def create_app() -> None:
    """PID Controller Web UI"""
    with ui.row().classes("w-full justify-between items-center"):
        with ui.row():
            ui.label("Serial Number")
            ui.label("HW version")
            ui.label("FW version")
        with ui.row():
            ui.button().props("icon=save flat round").tooltip("Save configuration")
            ui.button().props("icon=bug_report flat round").tooltip(
                "Dump and clear errors"
            )

            async def reboot(event) -> None:
                print("Reboot buttn clicked!")

            ui.button(on_click=reboot).props("icon=restart_alt flat round").tooltip(
                "Reboot"
            )

    with ui.row():
        for a, axis in enumerate(["Axis X", "Axis Y"]):
            with ui.card(), ui.column():
                _create_axis_column(a, axis)


def _create_axis_column(index, axis_name):
    ui.markdown(f"### {axis_name}")

    with ui.row().classes("w-full justify-between items-center"):
        mode = ui.toggle(["torque", "velocity", "position"], value="torque")
        ui.toggle(["undefined", "idle"])

    with ui.row():
        with ui.card().bind_visibility_from(mode, "value", value="torque"):
            _create_card_torque()
        with ui.card().bind_visibility_from(mode, "value", value="velocity"):
            _create_card_velocity()
        with ui.card().bind_visibility_from(mode, "value", value="position"):
            _create_card_position()

        with ui.column():
            _create_column_gain()

        with ui.column():
            _create_column_limit()


def _create_card_torque() -> None:
    ui.markdown("**Torque**")
    ui.number("input torque", value=6)

    with ui.row():
        ui.button().props("round flat icon=remove")
        ui.button().props("round flat icon=radio_button_unchecked")
        ui.button().props("round flat icon=add")


def _create_card_velocity() -> None:
    ui.markdown("**Velocity**")
    ui.number("input velocity", value=0)

    with ui.row():
        ui.button().props("round flat icon=fast_rewind")
        ui.button().props("round flat icon=stop")
        ui.button().props("round flat icon=fast_forward")


def _create_card_position() -> None:
    ui.markdown("**Position**")
    ui.number("input position", value=0)

    with ui.row():
        ui.button().props("round flat icon=skip_previous")
        ui.button().props("round flat icon=exposure_zero")
        ui.button().props("round flat icon=skip_next")


def _create_column_gain() -> None:

    ui.number("pos_gain", value=3.14, format="%.3f").props("outlined")
    ui.number("vel_gain", value=3.14, format="%.3f").props("outlined")
    ui.number("vel_integrator_gain", value=3.14, format="%.3f").props("outlined")
    ui.number("vel_differentiator_gain", value=3.14, format="%.3f").props("outlined")


def _create_column_limit() -> None:
    ui.number("vel_limit", value=3.14, format="%.3f").props("outlined")
    ui.number("enc_bandwidth", value=3.14, format="%.3f").props("outlined")
    ui.number("current_lim", value=3.14, format="%.1f").props("outlined")
    ui.number("cur_bandwidth", value=3.14, format="%.3f").props("outlined")
    ui.number("torque_lim", value=3.14, format="%.1f").props("outlined")
    ui.number("cur_range", value=3.14, format="%.1f").props("outlined")


@ui.page("/")
async def index() -> None:
    await create_app()


ui.run_with(app, title="PID Controller Web UI")


def main() -> None:
    """Start the WebUI application."""

    uvicorn.run("demo_openamp.webui.webui:app", reload=True)


if __name__ == "__main__":
    main()
