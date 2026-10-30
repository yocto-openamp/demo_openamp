#pragma once

#include <cstdint>

namespace commands {

// First Linux message on rpmsg-emw-IMU. This must match util_messages_to_M7.py.
constexpr char RPMSG_IMU_START[] = "start";

// Sent as one byte over RPMsg. These must match util_messages_to_M7.py.
enum class MSG_CMD_A53_to_M7 : uint8_t {
    IMU_START = 1,
};

} // namespace commands
