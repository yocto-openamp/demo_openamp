#include "lib_rpmsg.hpp"

#include <cerrno>
#include <cinttypes>

#include <zephyr/drivers/ipm.h>
#include <zephyr/logging/log.h>

#include <metal/sys.h>

#include <resource_table.h>

extern "C" {
#include <addr_translation.h>
}

LOG_MODULE_REGISTER(lib_rpmsg);

#if !DT_HAS_CHOSEN(zephyr_ipc_shm)
#error "Application requires zephyr,ipc_shm"
#endif

#if CONFIG_IPM_MAX_DATA_SIZE > 0
#define IPM_SEND(dev, wait, id, data, size) ipm_send(dev, wait, id, data, size)
#else
#define IPM_SEND(dev, wait, id, data, size) ipm_send(dev, wait, id, NULL, 0)
#endif

#define SHM_NODE DT_CHOSEN(zephyr_ipc_shm)
#define SHM_START_ADDR DT_REG_ADDR(SHM_NODE)
#define SHM_SIZE DT_REG_SIZE(SHM_NODE)

namespace rpmsg {

Endpoint::Endpoint(const char *channel, ReceiveHandler handler, void *context)
    : channel_(channel), handler_(handler), context_(context) {}

Endpoint::~Endpoint() {
    if (bound_) {
        rpmsg_destroy_ept(&endpoint_);
    }
}

int Endpoint::bind(struct rpmsg_device *device) {
    endpoint_.priv = this;
    const int result =
        rpmsg_create_ept(&endpoint_, device, channel_, RPMSG_ADDR_ANY,
                         RPMSG_ADDR_ANY, receive_callback, nullptr);
    bound_ = result == 0;
    return result;
}

int Endpoint::send(const void *data, std::size_t size) {
    if (!bound_) {
        return -ENOTCONN;
    }
    return rpmsg_send(&endpoint_, data, size);
}

int Endpoint::receive_callback(struct rpmsg_endpoint *, void *data,
                               std::size_t size, std::uint32_t source,
                               void *priv) {
    auto &endpoint = *static_cast<Endpoint *>(priv);
    return endpoint.handler_(endpoint, data, size, source, endpoint.context_);
}

Transport::Transport()
    : ipm_(DEVICE_DT_GET(DT_CHOSEN(zephyr_ipc))),
      shm_physmap_(SHM_START_ADDR) {
    k_sem_init(&ipm_sem_, 0, 1);
    k_sem_init(&ready_sem_, 0, 1);
}

int Transport::initialize() {
    initialization_result_ = initialize_platform();
    if (initialization_result_ == 0) {
        initialization_result_ = initialize_rpmsg();
    }
    k_sem_give(&ready_sem_);
    return initialization_result_;
}

int Transport::attach(Endpoint &endpoint) {
    k_sem_take(&ready_sem_, K_FOREVER);
    k_sem_give(&ready_sem_);
    if (initialization_result_ != 0) {
        return initialization_result_;
    }
    return endpoint.bind(rpmsg_device_);
}

[[noreturn]] void Transport::process_messages() {
    while (true) {
        k_sem_take(&ipm_sem_, K_FOREVER);
        LOG_DBG("Processing RPMsg notification");
        rproc_virtio_notified(virtio_device_.vdev, VRING1_ID);
    }
}

void Transport::ipm_callback(const struct device *, void *context,
                             std::uint32_t, volatile void *) {
    auto &transport = *static_cast<Transport *>(context);
    k_sem_give(&transport.ipm_sem_);
}

int Transport::mailbox_notify(void *priv, std::uint32_t id) {
    auto &transport = *static_cast<Transport *>(priv);
    std::uint32_t message = id << 16;

    LOG_DBG("Notify mailbox: vring=%" PRIu32 ", channel=%d", id,
            CONFIG_OPENAMP_RSC_TABLE_IPM_TX_ID);
    return IPM_SEND(transport.ipm_, 0, CONFIG_OPENAMP_RSC_TABLE_IPM_TX_ID,
                    &message, sizeof(message));
}

void Transport::new_service_callback(struct rpmsg_device *, const char *name,
                                     std::uint32_t source) {
    LOG_WRN("Unexpected name service announcement: %s at 0x%x", name, source);
}

int Transport::initialize_platform() {
    struct metal_init_params metal_params = METAL_INIT_DEFAULTS;
    int result = metal_init(&metal_params);
    if (result != 0) {
        LOG_ERR("metal_init failed: %d", result);
        return result;
    }

    metal_io_init(&shm_io_, reinterpret_cast<void *>(SHM_START_ADDR),
                  &shm_physmap_, SHM_SIZE, -1, 0,
                  addr_translation_get_ops(shm_physmap_));

    int resource_table_size;
    rsc_table_get(&resource_table_, &resource_table_size);
    resource_table_physmap_ =
        reinterpret_cast<metal_phys_addr_t>(resource_table_);
    metal_io_init(&resource_table_io_, resource_table_,
                  &resource_table_physmap_, resource_table_size, -1, 0, nullptr);

    if (!device_is_ready(ipm_)) {
        LOG_ERR("IPM device is not ready");
        return -ENODEV;
    }

    ipm_register_callback(ipm_, ipm_callback, this);
    result = ipm_set_enabled(ipm_, 1);
    if (result != 0) {
        LOG_ERR("ipm_set_enabled failed: %d", result);
    }
    return result;
}

int Transport::initialize_rpmsg() {
    auto *virtio = rproc_virtio_create_vdev(
        VIRTIO_DEV_DEVICE, VDEV_ID, rsc_table_to_vdev(resource_table_),
        &resource_table_io_, this, mailbox_notify, nullptr);
    if (virtio == nullptr) {
        LOG_ERR("Failed to create virtio device");
        return -ENODEV;
    }

    rproc_virtio_wait_remote_ready(virtio);

    auto *vring = rsc_table_get_vring0(resource_table_);
    int result = rproc_virtio_init_vring(
        virtio, 0, vring->notifyid, reinterpret_cast<void *>(vring->da),
        &shm_io_, vring->num, vring->align);
    if (result != 0) {
        LOG_ERR("Failed to initialize vring 0: %d", result);
        rproc_virtio_remove_vdev(virtio);
        return result;
    }

    vring = rsc_table_get_vring1(resource_table_);
    result = rproc_virtio_init_vring(
        virtio, 1, vring->notifyid, reinterpret_cast<void *>(vring->da),
        &shm_io_, vring->num, vring->align);
    if (result != 0) {
        LOG_ERR("Failed to initialize vring 1: %d", result);
        rproc_virtio_remove_vdev(virtio);
        return result;
    }

    result = rpmsg_init_vdev(&virtio_device_, virtio, new_service_callback,
                             &shm_io_, nullptr);
    if (result != 0) {
        LOG_ERR("rpmsg_init_vdev failed: %d", result);
        rproc_virtio_remove_vdev(virtio);
        return result;
    }

    rpmsg_device_ = rpmsg_virtio_get_rpmsg_device(&virtio_device_);
    return 0;
}

} // namespace rpmsg