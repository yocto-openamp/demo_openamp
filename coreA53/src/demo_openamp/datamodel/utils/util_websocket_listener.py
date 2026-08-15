from __future__ import annotations

import argparse
import asyncio
import json
import sys
import typing

websockets: typing.Any
try:
    import websockets
except ImportError:
    websockets = None


async def listen(url: str) -> None:
    if websockets is None:
        print(
            "Missing dependency: websockets. Install with '.venv/bin/pip install websockets'.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    print(f"Connecting to {url} ...")
    async with websockets.connect(url) as websocket:
        print("Connected. Waiting for notifications...")
        while True:
            message = await websocket.recv()
            try:
                parsed: typing.Any = json.loads(message)
            except json.JSONDecodeError:
                print(message)
                continue

            print(json.dumps(parsed, indent=2, sort_keys=True))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Listen to observer notifications from the WebSocket API."
    )
    parser.add_argument(
        "--url",
        default="ws://127.0.0.1:8000/customer_api/observer",
        help="WebSocket URL (default: %(default)s)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    try:
        asyncio.run(listen(url=args.url))
    except KeyboardInterrupt:
        print("Disconnected.")


if __name__ == "__main__":
    main()
