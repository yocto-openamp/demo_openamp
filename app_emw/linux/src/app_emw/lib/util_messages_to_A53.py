import enum


# These must match messages_to_A53.hpp.
class MSG_ID_M7_to_A53(enum.IntEnum):
    STATUS = 1
    IMU_STATUS = 2
    INTERRUPT_LINE_SENSOR = 3
