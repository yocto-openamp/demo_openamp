import ctypes
import enum


# These must match messages_to_A53.hpp.
class MSG_ID_M7_to_A53(enum.IntEnum):
    STATUS = 1
    IMU_STATUS = 2
    INTERRUPT_LINE_SENSOR = 3


# Packed msg_imu_status in messages_to_A53.hpp.
class MsgImuStatus(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("msg_id", ctypes.c_int32),
        ("timestamp", ctypes.c_uint64),  # us since boot
        ("measurement_count", ctypes.c_int32),
        ("measurement_count_error", ctypes.c_int32),
        ("x", ctypes.c_float),  # accel: um/s^2, gyro: urad/s
        ("y", ctypes.c_float),
        ("z", ctypes.c_float),
        ("accel", ctypes.c_uint8),  # 1: accel, 0: gyro
    ]


assert ctypes.sizeof(MsgImuStatus) == 33
