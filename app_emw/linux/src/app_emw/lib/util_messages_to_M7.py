import enum

# First Linux message on rpmsg-emw-IMU. This must match messages_to_M7.hpp.
RPMSG_IMU_START: bytes = b"start"


# Sent as one byte over RPMsg. These must match messages_to_M7.hpp.
class MSG_ID_A53_to_M7(enum.IntEnum):
    IMU_START = 1


def encode_msg(command: MSG_ID_A53_to_M7) -> bytes:
    return bytes([command])
