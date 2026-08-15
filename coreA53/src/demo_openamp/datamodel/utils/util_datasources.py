import asyncio
import os
import pathlib
import stat

from . import util_observer


async def namedpipe_task(observer: util_observer.Observer) -> None:

    filename = os.getenv("ENV_PIPE", None)
    if not filename:
        return

    namedpipe = pathlib.Path(filename)
    if not namedpipe.exists():
        os.mkfifo(namedpipe)

    mode = namedpipe.stat().st_mode
    if not stat.S_ISFIFO(mode):
        raise RuntimeError(f"{namedpipe} exists but is not a named pipe")

    fd = os.open(namedpipe, os.O_RDWR | os.O_NONBLOCK)

    def callback_read() -> None:
        data = os.read(fd, 4096)
        text = data.decode("utf-8", errors="replace").strip()
        print(f"{filename}: {text}")
        path, _, value_text = text.partition(" ")
        value = eval(value_text)
        observer.notify(path=path, value=value)

    loop = asyncio.get_running_loop()
    loop.add_reader(fd, callback_read)
