#!/usr/bin/env python3
"""Read ICM-45686 WHO_AM_I using Linux GPIO, not the ECSPI controller."""

import argparse
import math
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import gpiod
from gpiod.line import Direction, Value

GPIO_CHIP = "/dev/gpiochip4"
REMOTEPROC_STATE = Path("/sys/class/remoteproc/remoteproc0/state")
SCLK, MOSI, MISO, CS = 6, 7, 8, 9
LINE_NAMES = {
    SCLK: "SODIMM_196",
    MOSI: "SODIMM_200",
    MISO: "SODIMM_198",
    CS: "SODIMM_202",
}
WHO_AM_I_COMMAND = bytes((0xF2, 0x00))
EXPECTED_ID = 0xE9


def positive_int(text: str) -> int:
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return value


def positive_float(text: str) -> float:
    value = float(text)
    if not math.isfinite(value) or value <= 0:
        raise argparse.ArgumentTypeError("must be finite and greater than zero")
    return value


@contextmanager
def stopped_m7():
    state = REMOTEPROC_STATE.read_text().strip()
    if state not in ("running", "offline"):
        raise RuntimeError(f"Unexpected remoteproc state: {state!r}")
    restart = state == "running"
    if restart:
        print("Stopping M7 before requesting SPI pins.", flush=True)
        REMOTEPROC_STATE.write_text("stop")
    try:
        if REMOTEPROC_STATE.read_text().strip() != "offline":
            raise RuntimeError("M7 is not offline; refusing to drive its SPI pins")
        yield
    finally:
        if restart:
            print("Restarting M7 after releasing GPIO pins.", flush=True)
            REMOTEPROC_STATE.write_text("start")
            if REMOTEPROC_STATE.read_text().strip() != "running":
                raise RuntimeError("M7 did not return to the running state")


def transfer(request, tx: bytes, half_period: float) -> bytes:
    """Mode 0, MSB first; CS stays low over all transmitted bytes."""
    rx = bytearray()
    request.set_value(SCLK, Value.INACTIVE)
    request.set_value(CS, Value.INACTIVE)
    try:
        time.sleep(half_period)
        for byte in tx:
            received = 0
            for bit in range(7, -1, -1):
                request.set_value(
                    MOSI, Value.ACTIVE if byte & (1 << bit) else Value.INACTIVE
                )
                time.sleep(half_period)
                request.set_value(SCLK, Value.ACTIVE)
                time.sleep(half_period)
                received = (received << 1) | (request.get_value(MISO) == Value.ACTIVE)
                request.set_value(SCLK, Value.INACTIVE)
            rx.append(received)
        time.sleep(half_period)
    finally:
        request.set_value(CS, Value.ACTIVE)
    return bytes(rx)


def run(count: int, half_period: float) -> int:
    if os.geteuid() != 0:
        raise PermissionError("Run with sudo to access GPIO and stop/start the M7")
    with gpiod.Chip(GPIO_CHIP) as chip:
        for offset, expected in LINE_NAMES.items():
            info = chip.get_line_info(offset)
            if info.name != expected:
                raise RuntimeError(
                    f"{GPIO_CHIP} line {offset}: expected {expected}, got {info.name!r}"
                )
            if info.used:
                raise RuntimeError(
                    f"{expected} is already requested by {info.consumer!r}"
                )

    config = {
        (SCLK, MOSI): gpiod.LineSettings(
            direction=Direction.OUTPUT, output_value=Value.INACTIVE
        ),
        CS: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE),
        MISO: gpiod.LineSettings(direction=Direction.INPUT),
    }
    print(
        "GPIO SPI: mode 0, MSB first, 8-bit bytes, active-low CS\n"
        f"Half-period >= {half_period * 1e6:g} us; "
        "Linux scheduling and GPIO calls make the actual clock slower.\n"
        "TX: F2 00; expected RX: xx E9",
        flush=True,
    )
    matched = 0
    with stopped_m7():
        with gpiod.request_lines(
            GPIO_CHIP, consumer="bitbang-whoami", config=config
        ) as request:
            time.sleep(0.01)
            for attempt in range(1, count + 1):
                rx = transfer(request, WHO_AM_I_COMMAND, half_period)
                valid = rx[1] == EXPECTED_ID
                matched += valid
                print(
                    f"{attempt}/{count}: RX: {rx.hex(' ').upper()}; "
                    f"WHO_AM_I=0x{rx[1]:02X} "
                    f"{'OK' if valid else 'MISMATCH (expected 0xE9)'}",
                    flush=True,
                )
                if attempt < count:
                    time.sleep(0.2)
    print(f"Valid WHO_AM_I responses: {matched}/{count}", flush=True)
    return 0 if matched == count else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=positive_int, default=3)
    parser.add_argument(
        "--half-period-us",
        type=positive_float,
        default=500.0,
        help="minimum half-clock period in microseconds (default: 500, <= 1 kHz)",
    )
    args = parser.parse_args()
    try:
        return run(args.count, args.half_period_us / 1e6)
    except (OSError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
