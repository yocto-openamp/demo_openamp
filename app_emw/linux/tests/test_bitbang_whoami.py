import importlib.util
from pathlib import Path
from unittest.mock import Mock

import pytest
from gpiod.line import Value

SCRIPT = Path(__file__).parents[1] / "src" / "bitbang_whoami.py"
SPEC = importlib.util.spec_from_file_location("bitbang_whoami", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
bitbang = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bitbang)


def test_transfer_mode0_msb_first(monkeypatch):
    monkeypatch.setattr(bitbang.time, "sleep", lambda _: None)
    incoming = iter((0x00, 0xE9))
    events = []

    class Request:
        def __init__(self):
            self.bits = iter(())

        def set_value(self, pin, value):
            events.append((pin, value))

        def get_value(self, pin):
            assert pin == bitbang.MISO
            assert events[-1] == (bitbang.SCLK, Value.ACTIVE)
            bit = next(self.bits, None)
            if bit is None:
                byte = next(incoming)
                self.bits = iter((byte >> shift) & 1 for shift in range(7, -1, -1))
                bit = next(self.bits)
            return Value.ACTIVE if bit else Value.INACTIVE

    assert bitbang.transfer(Request(), b"\xf2\x00", 0.0005) == b"\x00\xe9"
    assert [value for pin, value in events if pin == bitbang.CS] == [
        Value.INACTIVE,
        Value.ACTIVE,
    ]
    assert [value.value for pin, value in events if pin == bitbang.MOSI] == [
        int(bit) for bit in "1111001000000000"
    ]
    assert events[:2] == [
        (bitbang.SCLK, Value.INACTIVE),
        (bitbang.CS, Value.INACTIVE),
    ]
    for index, (pin, _) in enumerate(events):
        if pin == bitbang.MOSI:
            assert events[index - 1] == (bitbang.SCLK, Value.INACTIVE) or index == 2
            assert events[index + 1] == (bitbang.SCLK, Value.ACTIVE)
            assert events[index + 2] == (bitbang.SCLK, Value.INACTIVE)


def test_transfer_releases_cs_on_error(monkeypatch):
    monkeypatch.setattr(bitbang.time, "sleep", lambda _: None)
    request = Mock()
    request.get_value.side_effect = OSError("GPIO read failed")
    with pytest.raises(OSError, match="GPIO read failed"):
        bitbang.transfer(request, b"\xf2\x00", 0.0005)
    request.set_value.assert_called_with(bitbang.CS, Value.ACTIVE)


@pytest.mark.parametrize("initial", ["running", "offline"])
@pytest.mark.parametrize("fail", [False, True])
def test_m7_state_restored(monkeypatch, initial, fail):
    state = Mock()
    current = [initial]
    writes = []
    state.read_text.side_effect = lambda: current[0]

    def write(command):
        writes.append(command)
        current[0] = {"stop": "offline", "start": "running"}[command]

    state.write_text.side_effect = write
    monkeypatch.setattr(bitbang, "REMOTEPROC_STATE", state)
    if fail:
        with pytest.raises(OSError, match="test error"), bitbang.stopped_m7():
            assert current[0] == "offline"
            raise OSError("test error")
    else:
        with bitbang.stopped_m7():
            assert current[0] == "offline"
    assert current[0] == initial
    assert writes == (["stop", "start"] if initial == "running" else [])


def test_unexpected_m7_state_rejected(monkeypatch):
    state = Mock()
    state.read_text.return_value = "crashed"
    monkeypatch.setattr(bitbang, "REMOTEPROC_STATE", state)
    with pytest.raises(RuntimeError, match="Unexpected remoteproc state"):
        with bitbang.stopped_m7():
            pytest.fail("must not drive pins")
    state.write_text.assert_not_called()


@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf"])
def test_invalid_clock_delay_rejected(value):
    with pytest.raises(bitbang.argparse.ArgumentTypeError):
        bitbang.positive_float(value)
