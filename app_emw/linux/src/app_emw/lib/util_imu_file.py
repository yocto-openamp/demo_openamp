import logging

import numpy

from app_emw.lib import util_constants

logger = logging.getLogger(__name__)

IMU_MEASUREMENTS_FILE = util_constants.DIRECTORY_DATA / "imu_measurements.bin"

# Packed measurement_t in main.cpp.
IMU_MEASUREMENT_DTYPE: numpy.dtype = numpy.dtype(
    [
        ("timestamp", "<u8"),  # us since boot
        ("x", "<i4"),  # accel: um/s^2, gyro: urad/s
        ("y", "<i4"),
        ("z", "<i4"),
        ("accel", "u1"),  # 1: accel, 0: gyro
    ]
)
IMU_MEASUREMENT_SIZE: int = IMU_MEASUREMENT_DTYPE.itemsize
