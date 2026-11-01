from __future__ import annotations

import logging

import uvicorn
from experiment_datadefinitions.utils_observer.util_message import MessageVerb
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from nicegui import ui

from app_emw.appweb import util_webui
from app_emw.lib import util_constants, util_logging, util_observer_push

logger = logging.getLogger(__name__)

util_logging.init_logging()

webui_state = util_webui.WebUIState()

bridge = util_observer_push.ObserverBridge(
    observer=webui_state.observer,
    verb_send=MessageVerb.SET_REQUEST,
    verb_receive=MessageVerb.NOTIFY,
)

app = FastAPI()


# Has to be defined before 'ui.run_with()' mounts NiceGUI on '/'.
@app.websocket(util_observer_push.ROUTE_OBSERVER_PUSH)
async def observer_push(websocket: WebSocket) -> None:
    await websocket.accept()
    logger.info("mallow-observer connected")
    try:
        await bridge.run(send=websocket.send_text, receive=websocket.receive_text)
    except WebSocketDisconnect:
        logger.info("mallow-observer disconnected")


@ui.page("/")
async def index() -> None:
    await util_webui.create_app(webui_state=webui_state)


ui.run_with(app, title="nexus-observer")


def main() -> None:
    """Start the WebUI application."""

    uvicorn.run(
        "app_emw.appweb.main_appweb_nexus:app",
        host="0.0.0.0",
        port=util_constants.NEXUS_PORT,
        reload=True,
    )


if __name__ == "__main__":
    main()
