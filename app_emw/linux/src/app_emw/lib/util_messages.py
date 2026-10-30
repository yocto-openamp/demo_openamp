import ctypes


# Common header of every RPMsg message. This must match messages.hpp.
class MsgHeader(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("msg_id", ctypes.c_int16),
        # Size of the whole message including this header.
        ("msg_size", ctypes.c_int16),
    ]


assert ctypes.sizeof(MsgHeader) == 4
