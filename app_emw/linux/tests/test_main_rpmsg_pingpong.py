import asyncio
import importlib.util
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

SCRIPT = Path(__file__).parents[1] / "src" / "main_rpmsg_pingpong.py"
SPEC = importlib.util.spec_from_file_location("main_rpmsg_pingpong", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
client = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(client)


def test_imu_starts_before_reading_and_receives_three_samples(capsys):
    samples = [b"X=1,Y=2,Z=3", b"X=4,Y=5,Z=6", b"X=7,Y=8,Z=9"]
    rpmsg = Mock()
    rpmsg.channel = Path("rpmsg-emw-IMU")
    rpmsg.endpoint = Path("/dev/rpmsg1")
    rpmsg.write = AsyncMock(return_value=5)

    async def read(size):
        rpmsg.write.assert_awaited_once_with(b"start")
        assert size == 512
        return samples.pop(0)

    rpmsg.read = AsyncMock(side_effect=read)

    asyncio.run(client.run_imu(rpmsg))

    assert rpmsg.read.await_count == 3
    output = capsys.readouterr().out
    assert "IMU sample 1: X=1,Y=2,Z=3" in output
    assert "IMU sample 3: X=7,Y=8,Z=9" in output


def test_imu_start_failure_is_reported():
    rpmsg = Mock()
    rpmsg.write = AsyncMock(side_effect=OSError("start failed"))
    rpmsg.read = AsyncMock()

    with pytest.raises(OSError, match="start failed"):
        asyncio.run(client.run_imu(rpmsg))

    rpmsg.read.assert_not_awaited()


def test_imu_closed_endpoint_is_reported():
    rpmsg = Mock()
    rpmsg.write = AsyncMock(return_value=5)
    rpmsg.read = AsyncMock(return_value=b"")

    with pytest.raises(RuntimeError, match="IMU RPMsg endpoint closed"):
        asyncio.run(client.run_imu(rpmsg))
