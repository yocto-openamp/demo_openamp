#include "lib_rpmsg.hpp"

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(demo_rpmsg);

#define APP_TASK_STACK_SIZE 2048

namespace {

rpmsg::Transport transport;

int echo(rpmsg::Endpoint &endpoint, const void *data, std::size_t size,
         std::uint32_t, void *) {
    LOG_INF("RPMsg received %u bytes: '%.*s'", static_cast<unsigned int>(size),
            static_cast<int>(size), static_cast<const char *>(data));
    return endpoint.send(data, size);
}

rpmsg::Endpoint endpoint{"rpmsg-demo-xyrx2", echo};

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

    return 0;
}
