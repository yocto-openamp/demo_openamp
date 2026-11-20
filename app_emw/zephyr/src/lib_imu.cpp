#include "lib_imu.hpp"

#include "generated_imu_status_struct.hpp"
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
constexpr uint8_t ICM45686_INT1_CONFIG0 = 0x16;
constexpr uint8_t ICM45686_INT1_CONFIG2 = 0x18;
// INT1_CONFIG0: route the UI Data Ready interrupt to INT1.
constexpr uint8_t ICM45686_INT1_EN_DRDY = 1u << 2;
// INT1_CONFIG2: active high, pulse mode, push-pull (as the Zephyr driver
// configures it in trigger mode).
constexpr uint8_t ICM45686_INT1_ACTIVE_HIGH = 1u << 0;
constexpr uint32_t ACCEL_MEASUREMENTS_PER_GYRO = 10;
constexpr int64_t IMU_STATUS_INTERVAL_MS = 1000;
// Matches accel-odr and gyro-odr of 12.5 Hz in prj_verdin_imx8mp.overlay.
constexpr int32_t IMU_SAMPLE_INTERVAL_MS = 80;

const spi_dt_spec imu_spi = SPI_DT_SPEC_GET(
    DT_NODELABEL(icm45686), SPI_OP_MODE_CONTROLLER | SPI_WORD_SET(8));

int read_register(uint8_t address, uint8_t &value) {
    uint8_t tx[] = {static_cast<uint8_t>(address | 0x80), 0};
    uint8_t rx[sizeof(tx)] = {};
    spi_buf tx_buffer = {tx, sizeof(tx)};
    spi_buf rx_buffer = {rx, sizeof(rx)};
    const spi_buf_set tx_buffers = {&tx_buffer, 1};
    const spi_buf_set rx_buffers = {&rx_buffer, 1};
    const int result = spi_transceive_dt(&imu_spi, &tx_buffers, &rx_buffers);
    value = rx[1];
    return result;
}

int write_register(uint8_t address, uint8_t value) {
    uint8_t tx[] = {address, value};
    spi_buf tx_buffer = {tx, sizeof(tx)};
    const spi_buf_set tx_buffers = {&tx_buffer, 1};
    return spi_write_dt(&imu_spi, &tx_buffers);
}

bool verify_sensor_id() {
    if (!spi_is_ready_dt(&imu_spi)) {
        LOG_ERR("ICM-45686 SPI bus or chip select is not ready");
        return false;
    }

    uint8_t device_id = 0;
    const int result = read_register(ICM45686_WHO_AM_I, device_id);
    if (result != 0) {
        LOG_ERR("ICM-45686 WHO_AM_I transfer failed: %d", result);
        return false;
    }
    if (device_id != ICM45686_DEVICE_ID) {
        LOG_ERR("ICM-45686 WHO_AM_I=0x%02x, expected 0x%02x",
                device_id, ICM45686_DEVICE_ID);
        return false;
    }

    LOG_INF("ICM-45686 WHO_AM_I=0x%02x", device_id);
    return true;
}

bool enable_drdy_interrupt_on_int1() {
    // INT1 pin behavior: active high, pulse mode, push-pull.
    int result = write_register(ICM45686_INT1_CONFIG2,
                                ICM45686_INT1_ACTIVE_HIGH);
    if (result != 0) {
        LOG_ERR("ICM-45686 INT1_CONFIG2 write failed: %d", result);
        return false;
    }

    // Enable the UI Data Ready interrupt on INT1.
    result = write_register(ICM45686_INT1_CONFIG0, ICM45686_INT1_EN_DRDY);
    if (result != 0) {
        LOG_ERR("ICM-45686 INT1_CONFIG0 write failed: %d", result);
        return false;
    }

    uint8_t readback = 0;
    result = read_register(ICM45686_INT1_CONFIG0, readback);
    if (result != 0 || readback != ICM45686_INT1_EN_DRDY) {
        LOG_ERR("ICM-45686 INT1_CONFIG0 readback=0x%02x (result %d), "
                "expected 0x%02x",
                readback, result, ICM45686_INT1_EN_DRDY);
        return false;
    }

    LOG_INF("ICM-45686 UI Data Ready interrupt enabled on INT1");
    return true;
}

#if LOG_IMU == 1
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
// Atomic: written by 'run()' and read by 'status()' in another thread.
atomic_t sample_fetch_err{0};
atomic_t sample_gap_max_us{0};
sensor_value accel[3];
sensor_value gyro[3];

void send_imu_status(rpmsg::Endpoint &status_endpoint) {
    imu_status.header.msg_id =
        static_cast<int16_t>(commands::MSG_ID_M7_to_A53::IMU_STATUS);
    imu_status.header.msg_size = sizeof(imu_status);
    imu_status.status.accel_x = sensor_value_to_float(&accel[0]);
    imu_status.status.accel_y = sensor_value_to_float(&accel[1]);
    imu_status.status.accel_z = sensor_value_to_float(&accel[2]);
    imu_status.status.gyro_x = sensor_value_to_float(&gyro[0]);
    imu_status.status.gyro_y = sensor_value_to_float(&gyro[1]);
    imu_status.status.gyro_z = sensor_value_to_float(&gyro[2]);
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

    const int result = endpoint_imu.send(&measurement, sizeof(measurement));
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

rpmsg::Endpoint endpoint_imu{"rpmsg-emw-IMU", start_imu};

ModelM7StatusIMU_t status() {
    return {static_cast<uint32_t>(atomic_get(&sample_fetch_err)),
            static_cast<uint32_t>(atomic_get(&sample_gap_max_us))};
}

void run(rpmsg::Endpoint &status_endpoint) {
    if (!verify_sensor_id()) {
        return;
    }

    const struct device *sensor = DEVICE_DT_GET(DT_NODELABEL(icm45686));
    if (!device_is_ready(sensor)) {
        LOG_ERR("ICM-45686 sensor is not ready");
        return;
    }

    if (!enable_drdy_interrupt_on_int1()) {
        return;
    }

    LOG_INF("Waiting for Linux to start IMU streaming");
    k_sem_take(&imu_ready, K_FOREVER);

    // NOTE: This timer is not synchronized with the sensor: A sample may
    // occasionally be read twice or missed, and timestamps are the read time.
    // The UI Data Ready interrupt is already output on INT1 (see
    // enable_drdy_interrupt_on_int1). The proper fix is to use it: Add
    // int-gpios to the overlay, enable a trigger mode such as
    // CONFIG_ICM45686_TRIGGER_GLOBAL_THREAD and read in the trigger handler.
    // This gives exactly one read per new sample and accurate timestamps, but
    // requires the INT1 pin of the sensor to be wired to a GPIO.
    k_timer sample_timer;
    k_timer_init(&sample_timer, nullptr, nullptr);
    k_timer_start(&sample_timer, K_MSEC(IMU_SAMPLE_INTERVAL_MS),
                  K_MSEC(IMU_SAMPLE_INTERVAL_MS));

    uint32_t accel_count = 0;
    uint64_t timestamp_previous = 0;
    int64_t time_imu_status_to_be_sent_ms = 0;
    while (true) {
        int result = sensor_sample_fetch(sensor);
        if (result != 0) {
            LOG_ERR("ICM-45686 sample fetch failed: %d", result);
            ++imu_status.status.measurement_count_error;
            atomic_inc(&sample_fetch_err);
        } else {
            const uint64_t timestamp = k_cyc_to_us_near64(k_cycle_get_64());

            if (timestamp_previous != 0) {
                const atomic_val_t gap_us =
                    static_cast<atomic_val_t>(timestamp - timestamp_previous);
                if (gap_us > atomic_get(&sample_gap_max_us)) {
                    atomic_set(&sample_gap_max_us, gap_us);
                }
            }
            timestamp_previous = timestamp;

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

        k_timer_status_sync(&sample_timer);
    }
}

} // namespace imu
