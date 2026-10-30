import enum

# First Linux message on rpmsg-emw-IMU. This must match commands.hpp.
RPMSG_IMU_START: bytes = b"start"


# Sent as one byte over RPMsg. These must match commands.hpp.
class ENUM_CMD_M7_2_A55(enum.IntEnum):
    STATUS = 1
    IMU_STATUS = 2
    INTERRUPT_LINE_SENSOR = 3


class ENUM_CMD_A55_2_M7(enum.IntEnum):
    IMU_START = 1


def encode_command(command: ENUM_CMD_A55_2_M7) -> bytes:
    return bytes([command])
