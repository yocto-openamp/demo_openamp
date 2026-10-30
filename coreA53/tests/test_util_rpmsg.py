import asyncio
import pathlib
import typing

from demo_openamp.openamp.util_rpmsg import Rpmsg


def test_concurrent_endpoint_discovery_is_serialized(
    tmp_path: pathlib.Path, monkeypatch: typing.Any
) -> None:
    control = tmp_path / "rpmsg_ctrl0"
    control.touch()
    channel = tmp_path / "channel"
    channel.mkdir()
    (channel / "dst").write_text("1")
    endpoints = [tmp_path / "rpmsg0", tmp_path / "rpmsg1"]
    for endpoint in endpoints:
        endpoint.touch()

    active_discoveries = 0
    maximum_active_discoveries = 0

    async def wait_for_channel(self: Rpmsg) -> pathlib.Path:
        return channel

    def find_control_device(self: Rpmsg) -> pathlib.Path:
        return control

    def endpoint_class_devices(self: Rpmsg) -> set[str]:
        nonlocal active_discoveries, maximum_active_discoveries
        active_discoveries += 1
        maximum_active_discoveries = max(
            maximum_active_discoveries, active_discoveries
        )
        return set()

    async def create_endpoint(
        self: Rpmsg,
        control_file: typing.BinaryIO,
        destination: int,
        previous_endpoints: set[str],
    ) -> pathlib.Path:
        nonlocal active_discoveries
        await asyncio.sleep(0.01)
        active_discoveries -= 1
        return endpoints.pop(0)

    monkeypatch.setattr(Rpmsg, "_wait_for_channel", wait_for_channel)
    monkeypatch.setattr(Rpmsg, "_find_control_device", find_control_device)
    monkeypatch.setattr(Rpmsg, "_endpoint_class_devices", endpoint_class_devices)
    monkeypatch.setattr(Rpmsg, "_create_endpoint", create_endpoint)

    async def open_endpoints() -> None:
        first = Rpmsg("channel-one")
        second = Rpmsg("channel-two")
        await asyncio.gather(first.__aenter__(), second.__aenter__())
        await asyncio.gather(
            first.__aexit__(None, None, None),
            second.__aexit__(None, None, None),
        )

    asyncio.run(open_endpoints())

    assert maximum_active_discoveries == 1
