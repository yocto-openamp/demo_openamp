#pragma once

#include <cstdint>

namespace commands {

// These must match util_messages_to_A53.py.
enum class MSG_ID_M7_to_A53 : uint8_t {
    STATUS = 1,
    IMU_STATUS = 2,
    INTERRUPT_LINE_SENSOR = 3,
};

// Sent 1:1 over RPMsg. This must match util_messages_to_A53.py.
typedef struct __attribute__((packed)) {
    int32_t msg_id;
    uint64_t timestamp; // us since boot
    int32_t measurement_count;
    int32_t measurement_count_error;
    float x; // accel: um/s^2, gyro: urad/s
    float y;
    float z;
    uint8_t accel; // 1: accel, 0: gyro
} msg_imu_status;

static_assert(sizeof(msg_imu_status) == 33, "msg_imu_status layout changed");

} // namespace commands
