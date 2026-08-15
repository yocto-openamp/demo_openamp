#pragma once

/**
 * @file
 * @brief C++ wrappers for RPMsg endpoints and the Zephyr OpenAMP transport.
 */

#include <cstddef>
#include <cstdint>

#include <zephyr/device.h>
#include <zephyr/kernel.h>

#include <metal/io.h>
#include <openamp/open_amp.h>

namespace rpmsg {

class Transport;

/**
 * @brief Represents an RPMsg channel endpoint with a receive callback.
 */
class Endpoint {
  public:
    using ReceiveHandler = int (*)(Endpoint &endpoint, const void *data,
                                   std::size_t size, std::uint32_t source,
                                   void *context);

    Endpoint(const char *channel, ReceiveHandler handler,
             void *context = nullptr);
    ~Endpoint();

    Endpoint(const Endpoint &) = delete;
    Endpoint &operator=(const Endpoint &) = delete;

    int send(const void *data, std::size_t size);

  private:
    friend class Transport;

    int bind(struct rpmsg_device *device);
    static int receive_callback(struct rpmsg_endpoint *endpoint, void *data,
                                std::size_t size, std::uint32_t source,
                                void *priv);

    struct rpmsg_endpoint endpoint_{};
    const char *channel_;
    ReceiveHandler handler_;
    void *context_;
    bool bound_{false};
};

  /**
   * @brief Initializes and runs the Zephyr OpenAMP RPMsg transport.
   */
class Transport {
  public:
    Transport();

    Transport(const Transport &) = delete;
    Transport &operator=(const Transport &) = delete;

    int initialize();
    int attach(Endpoint &endpoint);
    [[noreturn]] void process_messages();

  private:
    int initialize_platform();
    int initialize_rpmsg();
    static void ipm_callback(const struct device *device, void *context,
                             std::uint32_t id, volatile void *data);
    static int mailbox_notify(void *priv, std::uint32_t id);
    static void new_service_callback(struct rpmsg_device *device,
                                     const char *name, std::uint32_t source);

    struct k_sem ipm_sem_;
    struct k_sem ready_sem_;
    const struct device *const ipm_;
    metal_phys_addr_t shm_physmap_;
    metal_phys_addr_t resource_table_physmap_{};
    struct metal_io_region shm_io_{};
    struct metal_io_region resource_table_io_{};
    struct rpmsg_virtio_device virtio_device_{};
    struct rpmsg_device *rpmsg_device_{};
    void *resource_table_{};
    int initialization_result_{-EAGAIN};
};

} // namespace rpmsg