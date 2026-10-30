#pragma once

#include <cstdint>

namespace commands {

// Sent as one byte over RPMsg. These must match util_messages_to_A55.py.
enum class MSG_CMD_M7_to_A55 : uint8_t {
    STATUS = 1,
    IMU_STATUS = 2,
    INTERRUPT_LINE_SENSOR = 3,
};

} // namespace commands
