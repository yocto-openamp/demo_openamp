from __future__ import annotations

import asyncio
import contextlib
import fcntl
import os
import pathlib
import struct
import time
import types
import typing


def ioc(direction: int, ioctl_type: int, number: int, size: int) -> int:
    return (direction << 30) | (size << 16) | (ioctl_type << 8) | number


class Rpmsg:
    RPMSG_NAME_SIZE: int = 32
    RPMSG_ADDR_ANY: int = 0xFFFFFFFF
    RPMSG_CTRL_CLASS: pathlib.Path = pathlib.Path("/sys/class/rpmsg")
    RPMSG_BUS_DEVICES: pathlib.Path = pathlib.Path("/sys/bus/rpmsg/devices")

    RPMSG_ENDPOINT_INFO: struct.Struct = struct.Struct("32sII")
    RPMSG_CREATE_EPT_IOCTL: int = ioc(1, 0xB5, 1, RPMSG_ENDPOINT_INFO.size)

    def __init__(
        self,
        channel_name: str,
        control_name: pathlib.Path | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.channel_name = channel_name
        self.control_name = control_name
        self.timeout = timeout
        self.channel: pathlib.Path | None = None
        self.control: pathlib.Path | None = None
        self.endpoint: pathlib.Path | None = None
        self._endpoint_file: typing.BinaryIO | None = None
        self._stack: contextlib.ExitStack | None = None

    async def __aenter__(self) -> Rpmsg:
        self.channel, destination = await self._wait_for_channel()
        self.control = self._find_control_device()
        previous_endpoints = self._endpoint_class_devices()
        stack = contextlib.ExitStack()
        try:
            control_file = stack.enter_context(self.control.open("rb+", buffering=0))
            self.endpoint = await self._create_endpoint(
                control_file, destination, previous_endpoints
            )
            self._endpoint_file = stack.enter_context(
                self.endpoint.open("rb+", buffering=0)
            )
            os.set_blocking(self._endpoint_file.fileno(), False)
        except BaseException:
            stack.close()
            raise
        self._stack = stack
        return self

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> bool | None:
        assert self._stack is not None
        return self._stack.__exit__(exception_type, exception, traceback)

    async def read(self, size: int = -1) -> bytes:
        assert self._endpoint_file is not None
        file_descriptor = self._endpoint_file.fileno()
        while True:
            try:
                return os.read(file_descriptor, size)
            except BlockingIOError:
                await self._wait_for_file_descriptor(file_descriptor, writable=False)

    async def write(self, payload: bytes) -> int:
        assert self._endpoint_file is not None
        file_descriptor = self._endpoint_file.fileno()
        written = 0
        while written < len(payload):
            try:
                written += os.write(file_descriptor, payload[written:])
            except BlockingIOError:
                await self._wait_for_file_descriptor(file_descriptor, writable=True)
        return written

    async def _wait_for_file_descriptor(
        self, file_descriptor: int, writable: bool
    ) -> None:
        loop = asyncio.get_running_loop()
        ready = loop.create_future()
        add_handler = loop.add_writer if writable else loop.add_reader
        remove_handler = loop.remove_writer if writable else loop.remove_reader
        add_handler(file_descriptor, ready.set_result, None)
        try:
            await ready
        finally:
            remove_handler(file_descriptor)

    async def _wait_for_channel(self) -> tuple[pathlib.Path, int]:

        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            for device in self.RPMSG_BUS_DEVICES.glob("*"):
                try:
                    if (device / "name").read_text().strip() == self.channel_name:
                        return device, self._read_int(device / "dst")
                except (FileNotFoundError, ValueError):
                    continue
            await asyncio.sleep(0.1)
        raise TimeoutError(
            f"RPMsg channel {self.channel_name!r} did not appear within "
            f"{self.timeout:g} seconds"
        )

    def _find_control_device(self) -> pathlib.Path:
        if self.control_name is not None:
            path = pathlib.Path(self.control_name)
            if not path.exists():
                raise FileNotFoundError(path)
            return path

        controls = sorted(pathlib.Path("/dev").glob("rpmsg_ctrl*"))
        if len(controls) != 1:
            raise RuntimeError(
                f"expected one /dev/rpmsg_ctrl* device, found {len(controls)}; "
                "select one with --control"
            )
        return controls[0]

    async def _wait_for_endpoint(self, previous: set[str]) -> pathlib.Path:
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            created = self._endpoint_class_devices() - previous
            if len(created) == 1:
                device = pathlib.Path("/dev") / created.pop()
                if device.exists():
                    return device
            elif len(created) > 1:
                raise RuntimeError(
                    f"multiple RPMsg endpoints appeared: {sorted(created)}"
                )
            await asyncio.sleep(0.05)
        raise TimeoutError("RPMsg endpoint character device was not created")

    async def _create_endpoint(
        self,
        control_file: typing.BinaryIO,
        destination: int,
        previous_endpoints: set[str],
    ) -> pathlib.Path:
        endpoint_name = self.channel_name.encode()
        if len(endpoint_name) >= self.RPMSG_NAME_SIZE:
            raise ValueError(
                f"endpoint name must be shorter than {self.RPMSG_NAME_SIZE} bytes"
            )
        endpoint_info = self.RPMSG_ENDPOINT_INFO.pack(
            endpoint_name.ljust(self.RPMSG_NAME_SIZE, b"\0"),
            self.RPMSG_ADDR_ANY,
            destination,
        )
        fcntl.ioctl(control_file.fileno(), self.RPMSG_CREATE_EPT_IOCTL, endpoint_info)
        return await self._wait_for_endpoint(previous_endpoints)

    @staticmethod
    def _endpoint_class_devices() -> set[str]:
        return {
            path.name
            for path in Rpmsg.RPMSG_CTRL_CLASS.glob("rpmsg*")
            if not path.name.startswith("rpmsg_ctrl")
        }

    @staticmethod
    def _read_int(path: pathlib.Path) -> int:
        return int(path.read_text().strip(), 0)
