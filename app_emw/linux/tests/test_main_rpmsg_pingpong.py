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


def test_imu_starts_before_reading_and_writes_measurements_to_file(capsys, tmp_path):
    measurements = [bytes([i]) * client.IMU_MEASUREMENT_SIZE for i in range(6)]
    output_file = tmp_path / "imu.bin"
    rpmsg = Mock()
    rpmsg.channel = Path("rpmsg-emw-IMU")
    rpmsg.endpoint = Path("/dev/rpmsg1")
    rpmsg.write = AsyncMock(return_value=5)
    pending = list(measurements)

    async def read(size):
        rpmsg.write.assert_awaited_once_with(b"start")
        assert size == 512
        return pending.pop(0)

    rpmsg.read = AsyncMock(side_effect=read)

    asyncio.run(client.run_imu(rpmsg, output_file))

    assert rpmsg.read.await_count == 6
    assert output_file.read_bytes() == b"".join(measurements)
    assert f"Wrote 6 IMU measurements to {output_file}" in capsys.readouterr().out


def test_imu_start_failure_is_reported(tmp_path):
    rpmsg = Mock()
    rpmsg.write = AsyncMock(side_effect=OSError("start failed"))
    rpmsg.read = AsyncMock()

    with pytest.raises(OSError, match="start failed"):
        asyncio.run(client.run_imu(rpmsg, tmp_path / "imu.bin"))

    rpmsg.read.assert_not_awaited()


def test_imu_closed_endpoint_is_reported(tmp_path):
    rpmsg = Mock()
    rpmsg.write = AsyncMock(return_value=5)
    rpmsg.read = AsyncMock(return_value=b"")

    with pytest.raises(RuntimeError, match="IMU RPMsg endpoint closed"):
        asyncio.run(client.run_imu(rpmsg, tmp_path / "imu.bin"))


def test_imu_unexpected_payload_size_is_reported(tmp_path):
    rpmsg = Mock()
    rpmsg.write = AsyncMock(return_value=5)
    rpmsg.read = AsyncMock(return_value=b"X=1,Y=2,Z=3")

    with pytest.raises(RuntimeError, match="Unexpected IMU payload size 11"):
        asyncio.run(client.run_imu(rpmsg, tmp_path / "imu.bin"))
