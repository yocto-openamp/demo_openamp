import pathlib

import numpy as np
from app_emw.lib.util_constants import IMU_MEASUREMENTS_FILE
from app_emw.lib.util_imu_file import IMU_MEASUREMENT_DTYPE, IMU_MEASUREMENT_SIZE


def dump_imu_measurements(input_file: pathlib.Path) -> None:
    size = input_file.stat().st_size
    if size % IMU_MEASUREMENT_SIZE != 0:
        raise RuntimeError(f"Unexpected IMU file size {size}")

    measurements = np.fromfile(input_file, dtype=IMU_MEASUREMENT_DTYPE)

    # Accel values are in m/s^2, gyro values in rad/s.
    print(f"{'timestamp_us':>14} {'sensor':<6} {'x':>12} {'y':>12} {'z':>12}")
    for measurement in measurements:
        sensor = "accel" if measurement["accel"] else "gyro"
        x, y, z = (int(measurement[axis]) / 1e6 for axis in ("x", "y", "z"))
        print(
            f"{int(measurement['timestamp']):>14} {sensor:<6} {x:>12.6f} {y:>12.6f} {z:>12.6f}"
        )

    def print_rate(sensor: str) -> None:
        timestamps = measurements["timestamp"][
            measurements["accel"] == (sensor == "accel")
        ]
        if len(timestamps) < 2:
            return
        duration_us = int(timestamps[-1]) - int(timestamps[0])
        if duration_us > 0:
            rate = (len(timestamps) - 1) / (duration_us / 1e6)
            print(f"Measurements {sensor}: {rate:.0f} 1/s")

    print_rate("accel")
    print_rate("gyro")


def main() -> None:
    dump_imu_measurements(IMU_MEASUREMENTS_FILE)


if __name__ == "__main__":
    main()
