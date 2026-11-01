from __future__ import annotations

import asyncio
import collections.abc
import json
import logging
import os

from experiment_datadefinitions.utils_observer.util_message import Message, MessageVerb
from experiment_datadefinitions.utils_observer.util_observer import (
    Observer,
    Registration,
)
from websockets.asyncio.client import connect

from app_emw.lib import util_constants

logger = logging.getLogger(__name__)

ROUTE_OBSERVER_PUSH = "/observer_push"
NEXUS_URL = os.getenv(
    "ENV_NEXUS_URL",
    f"ws://127.0.0.1:{util_constants.NEXUS_PORT}{ROUTE_OBSERVER_PUSH}",
)

RECONNECT_INTERVAL_S = 5.0
QUEUE_SIZE = 1000
"""
Messages waiting to be sent: A stalled connection must not exhaust the memory.
"""


def message_to_text(message: Message) -> str:
    return json.dumps(
        {
            "topic": message.topic,
            "verb": message.verb.name,
            "topic_value": message.topic_value,
        }
    )


def message_from_text(text: str | bytes) -> Message:
    data = json.loads(text)
    return Message(
        topic=data["topic"],
        verb=MessageVerb[data["verb"]],
        topic_value=data["topic_value"],
    )


class ObserverBridge:
    """
    Integrates a websocket with the local observer.

    Only messages with 'verb_send' leave and only messages with 'verb_receive'
    enter. As these verbs differ, a message never travels back to its origin.
    """

    def __init__(
        self,
        observer: Observer,
        verb_send: MessageVerb,
        verb_receive: MessageVerb,
    ) -> None:
        assert verb_send != verb_receive
        self.observer = observer
        self.verb_send = verb_send
        self.verb_receive = verb_receive
        self._queues: set[asyncio.Queue[Message]] = set()

        observer.register_as_observer(
            registration=Registration(
                topic="/",
                callback=self._observer_callback,
            )
        )

    def _observer_callback(self, message: Message) -> None:
        if message.verb != self.verb_send:
            return

        for queue in self._queues:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                logger.warning(f"Queue full, dropped {message.topic}")

    def _deliver(self, message: Message) -> None:
        if message.verb != self.verb_receive:
            logger.warning(f"Ignored {message.verb.name}({message.topic})")
            return

        item = self.observer.items.get(message.topic)
        if item is None:
            logger.warning(f"Ignored unknown topic {message.topic}")
            return

        if message.verb == MessageVerb.SET_REQUEST:
            # A local GUI writes the value through 'bind_value', the observer does not.
            item.topic_value = message.topic_value

        self.observer.send_message(message=message)

    async def run(
        self,
        send: collections.abc.Callable[[str], collections.abc.Awaitable[None]],
        receive: collections.abc.Callable[[], collections.abc.Awaitable[str | bytes]],
    ) -> None:
        """
        Returns only by raising, typically when the websocket gets closed.
        """
        queue: asyncio.Queue[Message] = asyncio.Queue(maxsize=QUEUE_SIZE)

        async def loop_send() -> None:
            while True:
                message = await queue.get()
                await send(message_to_text(message))

        async def loop_receive() -> None:
            while True:
                self._deliver(message_from_text(await receive()))

        self._queues.add(queue)
        tasks = [asyncio.create_task(loop_send()), asyncio.create_task(loop_receive())]
        try:
            await asyncio.gather(*tasks)
        finally:
            self._queues.discard(queue)
            for task in tasks:
                task.cancel()


async def observer_push_task(observer: Observer, url: str = NEXUS_URL) -> None:
    """
    The mallow-observer side: Keep a connection to the nexus-observer.
    """
    bridge = ObserverBridge(
        observer=observer,
        verb_send=MessageVerb.NOTIFY,
        verb_receive=MessageVerb.SET_REQUEST,
    )

    while True:
        try:
            async with connect(url) as websocket:
                logger.info(f"Connected to {url}")
                await bridge.run(send=websocket.send, receive=websocket.recv)
        except Exception as e:
            logger.warning(f"Connection to {url} failed: {e!r}")

        await asyncio.sleep(RECONNECT_INTERVAL_S)
