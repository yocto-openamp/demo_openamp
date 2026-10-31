#include "generated_m7_status_channel.hpp"
#include "lib_imu.hpp"
#include "lib_rpmsg.hpp"
#include "messages.hpp"
#include "messages_to_A53.hpp"

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include <cstdint>

LOG_MODULE_REGISTER(app_emw);

#define APP_TASK_STACK_SIZE 2048

namespace {

constexpr int32_t M7_STATUS_INTERVAL_MS = 1000;

// Sent 1:1 over RPMsg: the msg_header followed by the status of each channel.
// This must match util_cmd_to_a53.py.
typedef struct __attribute__((packed)) {
    commands::msg_header header;
    ModelM7StatusChannel_t channel_cmd;
    ModelM7StatusChannel_t channel_imu;
} msg_m7_status_t;

K_SEM_DEFINE(cmd_ready, 0, 1);

rpmsg::Transport transport;

int echo(rpmsg::Endpoint &endpoint_cmd, const void *data, std::size_t size,
         std::uint32_t, void *) {
    LOG_INF("RPMsg received %u bytes: '%.*s'", static_cast<unsigned int>(size),
            static_cast<int>(size), static_cast<const char *>(data));
    k_sem_give(&cmd_ready);
    return endpoint_cmd.send(data, size);
}

rpmsg::Endpoint endpoint_cmd{"rpmsg-emw-CMD", echo};

void rpmsg_manager(void *, void *, void *) {
    if (transport.initialize() != 0) {
        return;
    }
    transport.process_messages();
}

void imu_runner(void *, void *, void *) { imu::run(endpoint_cmd); }

ModelM7StatusChannel_t channel_status(const rpmsg::Endpoint &endpoint) {
    const rpmsg::Counters counters = endpoint.counters();
    return {counters.tx_ok, counters.tx_err, counters.tx_last_err,
            counters.rx_ok};
}

void send_m7_status() {
    msg_m7_status_t status = {};
    status.header.msg_id =
        static_cast<int16_t>(commands::MSG_ID_M7_to_A53::STATUS);
    status.header.msg_size = sizeof(status);
    status.channel_cmd = channel_status(endpoint_cmd);
    status.channel_imu = channel_status(imu::endpoint_imu);

    const int result = endpoint_cmd.send(&status, sizeof(status));
    if (result < 0) {
        LOG_WRN("Could not send M7 status: %d", result);
    } else if (static_cast<std::size_t>(result) != sizeof(status)) {
        LOG_WRN("Incomplete M7 status: %d of %u bytes", result,
                static_cast<unsigned int>(sizeof(status)));
    }
}

// In its own thread: The status must keep flowing if the IMU fails or hangs.
void m7_status_runner(void *, void *, void *) {
    // The first Linux message lets OpenAMP learn the CMD return address.
    k_sem_take(&cmd_ready, K_FOREVER);

    while (true) {
        // Sleep first to stay out of the Linux ping-pong on this channel.
        k_sleep(K_MSEC(M7_STATUS_INTERVAL_MS));
        send_m7_status();
    }
}

K_THREAD_DEFINE(rpmsg_manager_thread, APP_TASK_STACK_SIZE, rpmsg_manager, NULL, NULL, NULL,
                K_PRIO_COOP(8), 0, SYS_FOREVER_MS);
K_THREAD_DEFINE(imu_thread, APP_TASK_STACK_SIZE, imu_runner, NULL, NULL, NULL,
                K_PRIO_PREEMPT(0), 0, SYS_FOREVER_MS);
K_THREAD_DEFINE(m7_status_thread, APP_TASK_STACK_SIZE, m7_status_runner, NULL,
                NULL, NULL, K_PRIO_PREEMPT(1), 0, SYS_FOREVER_MS);

} // namespace

int main(void) {
    LOG_INF("Starting Verdin iMX8MP OpenAMP RpMsg demo");

    k_thread_start(rpmsg_manager_thread);

    int result = transport.attach(endpoint_cmd);
    if (result != 0) {
        LOG_ERR("Could not create CMD RPMsg endpoint_cmd: %d", result);
    } else {
        LOG_INF("Linux RPMsg App endpoint_cmd is ready");
    }

    result = transport.attach(imu::endpoint_imu);
    if (result != 0) {
        LOG_ERR("Could not create IMU RPMsg endpoint_imu: %d", result);
    } else {
        LOG_INF("Linux RPMsg IMU endpoint_imu is ready");
    }

    k_thread_start(imu_thread);
    k_thread_start(m7_status_thread);

    k_sleep(K_SECONDS(5));

    LOG_INF("Done");

    return 0;
}
