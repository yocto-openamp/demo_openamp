#include "lib_rpmsg.hpp"

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/drivers/spi.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include <cstdint>

LOG_MODULE_REGISTER(app_emw);

#define APP_TASK_STACK_SIZE 2048

namespace {

constexpr uint8_t ICM45686_WHO_AM_I = 0x72;
constexpr uint8_t ICM45686_DEVICE_ID = 0xe9;

bool verify_sensor_id() {
    const spi_dt_spec spi = SPI_DT_SPEC_GET(
        DT_NODELABEL(icm45686), SPI_OP_MODE_MASTER | SPI_WORD_SET(8));
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

rpmsg::Transport transport;

int echo(rpmsg::Endpoint &endpoint, const void *data, std::size_t size,
         std::uint32_t, void *) {
    LOG_INF("RPMsg received %u bytes: '%.*s'", static_cast<unsigned int>(size),
            static_cast<int>(size), static_cast<const char *>(data));
    return endpoint.send(data, size);
}

rpmsg::Endpoint endpoint{"rpmsg-emw-xyrx2", echo};

void manager(void *, void *, void *) {
    if (transport.initialize() != 0) {
        return;
    }
    transport.process_messages();
}

void client(void *, void *, void *) {
    const int result = transport.attach(endpoint);
    if (result != 0) {
        LOG_ERR("Could not create RPMsg endpoint: %d", result);
    } else {
        LOG_INF("Linux RPMsg endpoint is ready");
    }
}

K_THREAD_DEFINE(manager_thread, APP_TASK_STACK_SIZE, manager, NULL, NULL, NULL,
                K_PRIO_COOP(8), 0, SYS_FOREVER_MS);
K_THREAD_DEFINE(client_thread, APP_TASK_STACK_SIZE, client, NULL, NULL, NULL,
                K_PRIO_COOP(7), 0, SYS_FOREVER_MS);

} // namespace

int main(void) {
    LOG_INF("Starting Verdin iMX8MP OpenAMP RpMsg demo");

    k_thread_start(manager_thread);
    k_thread_start(client_thread);

    if (!verify_sensor_id()) {
        return 0;
    }

    const struct device *sensor = DEVICE_DT_GET(DT_NODELABEL(icm45686));
    if (!device_is_ready(sensor)) {
        LOG_ERR("ICM-45686 sensor is not ready");
        return 0;
    }

    while (true) {
        int result = sensor_sample_fetch(sensor);
        if (result != 0) {
            LOG_ERR("ICM-45686 sample fetch failed: %d", result);
        } else {
            sensor_value accel[3];
            result = sensor_channel_get(sensor, SENSOR_CHAN_ACCEL_XYZ, accel);
            if (result != 0) {
                LOG_ERR("ICM-45686 accelerometer read failed: %d", result);
            } else {
                const auto x = format_sensor_value(accel[0]);
                const auto y = format_sensor_value(accel[1]);
                const auto z = format_sensor_value(accel[2]);

                LOG_INF("Accel [m/s^2]: X=%s%d.%06u, Y=%s%d.%06u, Z=%s%d.%06u",
                        x.sign, x.whole, x.fraction, y.sign, y.whole,
                        y.fraction, z.sign, z.whole, z.fraction);
            }

            sensor_value gyro[3];
            result = sensor_channel_get(sensor, SENSOR_CHAN_GYRO_XYZ, gyro);
            if (result != 0) {
                LOG_ERR("ICM-45686 gyroscope read failed: %d", result);
            } else {
                const auto x = format_sensor_value(gyro[0]);
                const auto y = format_sensor_value(gyro[1]);
                const auto z = format_sensor_value(gyro[2]);

                LOG_INF("Gyro [rad/s]: X=%s%d.%06u, Y=%s%d.%06u, Z=%s%d.%06u",
                        x.sign, x.whole, x.fraction, y.sign, y.whole,
                        y.fraction, z.sign, z.whole, z.fraction);
            }
        }

        k_sleep(K_SECONDS(1));
    }

    return 0;
}
