#include "lib_imu.hpp"

#include "generated_imu_status.hpp"
#include "messages.hpp"
#include "messages_to_A53.hpp"
#include "messages_to_M7.hpp"

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/drivers/spi.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include <cstdint>
#include <cstring>

LOG_MODULE_REGISTER(lib_imu);

#define LOG_IMU 0

namespace imu {
namespace {

constexpr uint8_t ICM45686_WHO_AM_I = 0x72;
constexpr uint8_t ICM45686_DEVICE_ID = 0xe9;
constexpr uint32_t ACCEL_MEASUREMENTS_PER_GYRO = 10;
constexpr int64_t IMU_STATUS_INTERVAL_MS = 1000;

bool verify_sensor_id() {
    const spi_dt_spec spi = SPI_DT_SPEC_GET(
        DT_NODELABEL(icm45686), SPI_OP_MODE_CONTROLLER | SPI_WORD_SET(8));
    if (!spi_is_ready_dt(&spi)) {
        LOG_ERR("ICM-45686 SPI bus or chip select is not ready");
        return false;
    }

    uint8_t tx[] = {static_cast<uint8_t>(ICM45686_WHO_AM_I | 0x80), 0};
    uint8_t rx[sizeof(tx)] = {};
    spi_buf tx_buffer = {tx, sizeof(tx)};
    spi_buf rx_buffer = {rx, sizeof(rx)};
    const spi_buf_set tx_buffers = {&tx_buffer, 1};
    const spi_buf_set rx_buffers = {&rx_buffer, 1};
    const int result = spi_transceive_dt(&spi, &tx_buffers, &rx_buffers);
    if (result != 0) {
        LOG_ERR("ICM-45686 WHO_AM_I transfer failed: %d", result);
        return false;
    }
    if (rx[1] != ICM45686_DEVICE_ID) {
        LOG_ERR("ICM-45686 WHO_AM_I=0x%02x, expected 0x%02x",
                rx[1], ICM45686_DEVICE_ID);
        return false;
    }

    LOG_INF("ICM-45686 WHO_AM_I=0x%02x", rx[1]);
    return true;
}

struct FormattedSensorValue {
    const char *sign;
    int32_t whole;
    uint32_t fraction;
};

#if LOG_IMU == 1
FormattedSensorValue format_sensor_value(const sensor_value &value) {
    const int64_t millionths =
        static_cast<int64_t>(value.val1) * 1000000 + value.val2;
    const bool negative = millionths < 0;
    const uint64_t magnitude =
        negative ? static_cast<uint64_t>(-millionths)
                 : static_cast<uint64_t>(millionths);

    return {negative ? "-" : "",
            static_cast<int32_t>(magnitude / 1000000),
            static_cast<uint32_t>(magnitude % 1000000)};
}
#endif // LOG_IMU

K_SEM_DEFINE(imu_ready, 0, 1);

int start_imu(rpmsg::Endpoint &, const void *data, std::size_t size,
              std::uint32_t, void *) {
    const auto &command = commands::RPMSG_IMU_START;
    if (size != sizeof(command) - 1 ||
        std::memcmp(data, command, sizeof(command) - 1) != 0) {
        LOG_WRN("Unexpected IMU RPMsg command");
        return 0;
    }

    k_sem_give(&imu_ready);
    return 0;
}

// Sent 1:1 over RPMsg. This must match util_imu_measurmenets.py.
typedef struct __attribute__((packed)) {
    uint64_t timestamp; // us since boot
    int32_t x;          // accel: um/s^2, gyro: urad/s
    int32_t y;
    int32_t z;
    uint8_t accel; // 1: accel, 0: gyro
} measurement_t;

static_assert(sizeof(measurement_t) == 21, "measurement_t layout changed");

// Sent 1:1 over RPMsg: the msg_header followed by the generated IMU status.
// This must match main_app_emw.py.
typedef struct __attribute__((packed)) {
    commands::msg_header header;
    ModelImuStatus_t status;
} msg_imu_status_t;

msg_imu_status_t imu_status = {};
sensor_value accel[3];
sensor_value gyro[3];

void send_imu_status(rpmsg::Endpoint &status_endpoint) {
    imu_status.header.msg_id =
        static_cast<int16_t>(commands::MSG_ID_M7_to_A53::IMU_STATUS);
    imu_status.header.msg_size = sizeof(imu_status);
    imu_status.status.accel_x =
        static_cast<double>(sensor_value_to_micro(&accel[0]));
    imu_status.status.accel_y =
        static_cast<double>(sensor_value_to_micro(&accel[1]));
    imu_status.status.accel_z =
        static_cast<double>(sensor_value_to_micro(&accel[2]));
    imu_status.status.gyro_x =
        static_cast<double>(sensor_value_to_micro(&gyro[0]));
    imu_status.status.gyro_y =
        static_cast<double>(sensor_value_to_micro(&gyro[1]));
    imu_status.status.gyro_z =
        static_cast<double>(sensor_value_to_micro(&gyro[2]));
    const int result = status_endpoint.send(&imu_status, sizeof(imu_status));
    if (result < 0) {
        LOG_WRN("Could not send IMU status: %d", result);
    } else if (static_cast<std::size_t>(result) != sizeof(imu_status)) {
        LOG_WRN("Incomplete IMU status: %d of %u bytes", result,
                static_cast<unsigned int>(sizeof(imu_status)));
    }
}

void send_measurement(uint64_t timestamp, const sensor_value (&values)[3],
                      bool is_accel) {
    const measurement_t measurement = {
        timestamp, static_cast<int32_t>(sensor_value_to_micro(&values[0])),
        static_cast<int32_t>(sensor_value_to_micro(&values[1])),
        static_cast<int32_t>(sensor_value_to_micro(&values[2])), is_accel};

    const int result = endpoint.send(&measurement, sizeof(measurement));
    if (result < 0) {
        LOG_WRN("Could not send IMU RPMsg measurement: %d", result);
        ++imu_status.status.measurement_count_error;
    } else if (static_cast<std::size_t>(result) != sizeof(measurement)) {
        LOG_WRN("Incomplete IMU RPMsg measurement: %d of %u bytes", result,
                static_cast<unsigned int>(sizeof(measurement)));
        ++imu_status.status.measurement_count_error;
    } else {
        ++imu_status.status.measurement_count;
    }
}

} // namespace

rpmsg::Endpoint endpoint{"rpmsg-emw-IMU", start_imu};

void run(rpmsg::Endpoint &status_endpoint) {
    if (!verify_sensor_id()) {
        return;
    }

    const struct device *sensor = DEVICE_DT_GET(DT_NODELABEL(icm45686));
    if (!device_is_ready(sensor)) {
        LOG_ERR("ICM-45686 sensor is not ready");
        return;
    }

    LOG_INF("Waiting for Linux to start IMU streaming");
    k_sem_take(&imu_ready, K_FOREVER);

    uint32_t accel_count = 0;
    int64_t time_imu_status_to_be_sent_ms = 0;
    while (true) {
        int result = sensor_sample_fetch(sensor);
        if (result != 0) {
            LOG_ERR("ICM-45686 sample fetch failed: %d", result);
            ++imu_status.status.measurement_count_error;
        } else {
            const uint64_t timestamp = k_cyc_to_us_near64(k_cycle_get_64());

            result = sensor_channel_get(sensor, SENSOR_CHAN_ACCEL_XYZ, accel);
            if (result != 0) {
                LOG_ERR("ICM-45686 accelerometer read failed: %d", result);
                ++imu_status.status.measurement_count_error;
            } else {
#if LOG_IMU == 1
                const auto x = format_sensor_value(accel[0]);
                const auto y = format_sensor_value(accel[1]);
                const auto z = format_sensor_value(accel[2]);

                LOG_INF("Accel [m/s^2]: X=%s%d.%06u, Y=%s%d.%06u, Z=%s%d.%06u",
                        x.sign, x.whole, x.fraction, y.sign, y.whole,
                        y.fraction, z.sign, z.whole, z.fraction);
#endif // LOG_IMU
                send_measurement(timestamp, accel, true);
            }

            if (++accel_count >= ACCEL_MEASUREMENTS_PER_GYRO) {
                accel_count = 0;

                result = sensor_channel_get(sensor, SENSOR_CHAN_GYRO_XYZ, gyro);
                if (result != 0) {
                    LOG_ERR("ICM-45686 gyroscope read failed: %d", result);
                    ++imu_status.status.measurement_count_error;
                } else {
#if LOG_IMU == 1
                    const auto x = format_sensor_value(gyro[0]);
                    const auto y = format_sensor_value(gyro[1]);
                    const auto z = format_sensor_value(gyro[2]);

                    LOG_INF("Gyro [rad/s]: X=%s%d.%06u, Y=%s%d.%06u, "
                            "Z=%s%d.%06u",
                            x.sign, x.whole, x.fraction, y.sign, y.whole,
                            y.fraction, z.sign, z.whole, z.fraction);
#endif // LOG_IMU
                    send_measurement(timestamp, gyro, false);
                }
            }
        }

        if (k_uptime_get() >= time_imu_status_to_be_sent_ms) {
            send_imu_status(status_endpoint);
            time_imu_status_to_be_sent_ms =
                k_uptime_get() + IMU_STATUS_INTERVAL_MS;
        }

        k_sleep(K_USEC(1));
    }
}

} // namespace imu
