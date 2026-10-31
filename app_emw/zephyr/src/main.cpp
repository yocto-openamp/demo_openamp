#include "lib_imu.hpp"
#include "lib_rpmsg.hpp"

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include <cstdint>

LOG_MODULE_REGISTER(app_emw);

#define APP_TASK_STACK_SIZE 2048

namespace {

rpmsg::Transport transport;

int echo(rpmsg::Endpoint &endpoint_cmd, const void *data, std::size_t size,
         std::uint32_t, void *) {
    LOG_INF("RPMsg received %u bytes: '%.*s'", static_cast<unsigned int>(size),
            static_cast<int>(size), static_cast<const char *>(data));
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

K_THREAD_DEFINE(rpmsg_manager_thread, APP_TASK_STACK_SIZE, rpmsg_manager, NULL, NULL, NULL,
                K_PRIO_COOP(8), 0, SYS_FOREVER_MS);
K_THREAD_DEFINE(imu_thread, APP_TASK_STACK_SIZE, imu_runner, NULL, NULL, NULL,
                K_PRIO_PREEMPT(0), 0, SYS_FOREVER_MS);

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

    k_sleep(K_SECONDS(5));

    LOG_INF("Done");

    return 0;
}
