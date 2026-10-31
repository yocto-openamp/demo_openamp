#pragma once

#include "lib_rpmsg.hpp"

namespace imu {

// Endpoint streaming the IMU measurements; must be attached to the transport.
extern rpmsg::Endpoint endpoint_imu;

// Verifies the ICM-45686, waits for Linux to start the streaming, then reads
// and sends measurements forever. The IMU status is sent periodically over
// 'status_endpoint'. Returns only if the sensor is not usable.
void run(rpmsg::Endpoint &status_endpoint);

} // namespace imu
