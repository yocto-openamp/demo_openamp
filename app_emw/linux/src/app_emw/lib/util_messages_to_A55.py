import enum


# Sent as one byte over RPMsg. These must match messages_to_A55.hpp.
class MSG_CMD_M7_to_A55(enum.IntEnum):
    STATUS = 1
    IMU_STATUS = 2
    INTERRUPT_LINE_SENSOR = 3
