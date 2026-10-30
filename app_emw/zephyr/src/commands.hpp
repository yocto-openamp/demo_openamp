#pragma once

#include <cstdint>

namespace commands {

// First Linux message on rpmsg-emw-IMU. This must match util_commands.py.
constexpr char RPMSG_IMU_START[] = "start";

// Sent as one byte over RPMsg. These must match util_commands.py.
enum class ENUM_CMD_M7_2_A55 : uint8_t {
    STATUS = 1,
    IMU_STATUS = 2,
    INTERRUPT_LINE_SENSOR = 3,
};

enum class ENUM_CMD_A55_2_M7 : uint8_t {
    IMU_START = 1,
};

} // namespace commands
