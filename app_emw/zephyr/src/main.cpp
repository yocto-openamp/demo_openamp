#include "generated_git_version.hpp"
// Keep this order: generated_m7_status_struct.hpp references the other structs.
#include "generated_m7_status_channel_struct.hpp"
#include "generated_m7_status_imu_struct.hpp"
#include "generated_m7_status_zephyr_struct.hpp"
#include "generated_m7_status_struct.hpp"
#include "lib_imu.hpp"
#include "lib_rpmsg.hpp"
#include "messages.hpp"
#include "messages_to_A53.hpp"

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include <cstdint>
#include <cstring>

LOG_MODULE_REGISTER(app_emw);

#define APP_TASK_STACK_SIZE 2048

namespace {

constexpr int32_t M7_STATUS_INTERVAL_MS = 1000;

static_assert(sizeof(GIT_VERSION) <= sizeof(ModelM7Status_t::git_commit),
              "GIT_VERSION does not fit into git_commit");

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
    // Sent 1:1 over RPMsg: the msg_header followed by the generated M7 status.
    struct __attribute__((packed)) {
        commands::msg_header header;
        ModelM7Status_t status;
    } msg = {};
    msg.header.msg_id =
        static_cast<int16_t>(commands::MSG_ID_M7_to_A53::STATUS);
    msg.header.msg_size = sizeof(msg);
    std::memcpy(msg.status.git_commit, GIT_VERSION, sizeof(GIT_VERSION));
    msg.status.status_zephyr.mailbox_notify_err = transport.mailbox_notify_err();
    msg.status.status_zephyr.mailbox_last_error_code =
        transport.mailbox_last_error_code();
    msg.status.status_zephyr.mailbox_notify_coalesced =
        transport.mailbox_notify_coalesced();
    msg.status.status_imu = imu::status();
    msg.status.channel_cmd = channel_status(endpoint_cmd);
    msg.status.channel_imu = channel_status(imu::endpoint_imu);

    const int result = endpoint_cmd.send(&msg, sizeof(msg));
    if (result < 0) {
        LOG_WRN("Could not send M7 status: %d", result);
    } else if (static_cast<std::size_t>(result) != sizeof(msg)) {
        LOG_WRN("Incomplete M7 status: %d of %u bytes", result,
                static_cast<unsigned int>(sizeof(msg)));
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

    if (true) {
        k_sleep(K_FOREVER);
    } else {
        k_sleep(K_SECONDS(5));
    
        LOG_INF("Done");
    }

    return 0;
}
