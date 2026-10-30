#pragma once

#include <cstdint>

namespace commands {

// These must match util_messages_to_A53.py.
enum class MSG_ID_M7_to_A53 : uint8_t {
    STATUS = 1,
    IMU_STATUS = 2,
    INTERRUPT_LINE_SENSOR = 3,
};

} // namespace commands
