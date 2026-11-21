#include "lib_irq_throttler.hpp"

#include "messages.hpp"

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include <cstddef>

LOG_MODULE_REGISTER(lib_irq_throttler);

namespace {

// Above the main-loop threads so interrupt signals go out with low latency.
constexpr int THREAD_PRIORITY = K_PRIO_PREEMPT(0);

uint64_t timestamp_us() { return k_cyc_to_us_near64(k_cycle_get_64()); }

} // namespace

IrqThrottler::IrqThrottler(rpmsg::Endpoint &endpoint, const Config &config)
    : endpoint_(&endpoint),
      irq_min_interval_us_(config.irq_min_interval_us),
      livesign_min_delay_us_(config.livesign_min_delay_us),
      message_id_(config.message_id) {
    k_sem_init(&sem_, 0, 1);
    k_thread_create(&thread_, stack_, K_KERNEL_STACK_SIZEOF(stack_),
                    thread_entry, this, nullptr, nullptr, THREAD_PRIORITY, 0,
                    K_NO_WAIT);
    k_thread_name_set(&thread_, "irq_throttler");
}

void IrqThrottler::irq() {
    irq_timestamp_us_ = timestamp_us();
    atomic_set(&irq_occurred_, 1);
    atomic_inc(&irq_counter_);
    k_sem_give(&sem_);
}

void IrqThrottler::thread_entry(void *self, void *, void *) {
    static_cast<IrqThrottler *>(self)->run();
}

void IrqThrottler::run() {
    // [us] When the last interrupt signal was sent: the rate limit. The
    // check also applies to the first interrupt, using the initial 0.
    uint64_t last_interrupt_send_us = 0;
    // The number of interrupt signals sent: derives the dropped count.
    uint32_t interrupt_send_count = 0;

    while (true) {
        // Taken: an interrupt occurred. Timeout: a livesign is due.
        const bool is_interrupt =
            k_sem_take(&sem_, K_USEC(livesign_min_delay_us_)) == 0;
        if (is_interrupt) {
            const uint64_t now_us = timestamp_us();
            if (now_us - last_interrupt_send_us < irq_min_interval_us_) {
                // Rate limit: drop this interrupt signal.
                continue;
            }
            last_interrupt_send_us = now_us;
            interrupt_send_count++;
        }
        send_signal(is_interrupt, interrupt_send_count);
    }
}

// Reads the 64-bit timestamp written by irq(): the copy may tear when an
// interrupt updates it mid-read, so retry whenever an interrupt occurred.
uint64_t IrqThrottler::read_irq_timestamp_us() {
    uint64_t snapshot_us;
    do {
        atomic_set(&irq_occurred_, 0);
        snapshot_us = irq_timestamp_us_;
    } while (atomic_get(&irq_occurred_));
    return snapshot_us;
}

void IrqThrottler::send_signal(const bool is_interrupt,
                               const uint32_t interrupt_send_count) {
    // Sent 1:1 over RPMsg: the msg_header followed by the irq_signal.
    struct __attribute__((packed)) {
        commands::msg_header header;
        IrqX19_7_t signal;
    } msg = {};
    msg.header.msg_id = static_cast<int16_t>(message_id_);
    msg.header.msg_size = sizeof(msg);
    msg.signal.irq_timestamp_us = read_irq_timestamp_us();
    const uint32_t irq_counter =
        static_cast<uint32_t>(atomic_get(&irq_counter_));
    msg.signal.irq_counter = static_cast<uint16_t>(irq_counter);
    // Dropped: every interrupt that did not result in a sent signal.
    msg.signal.irq_dropped_counter =
        static_cast<uint16_t>(irq_counter - interrupt_send_count);
    msg.signal.is_interrupt = is_interrupt;

    const int result = endpoint_->send(&msg, sizeof(msg));
    if (result < 0) {
        LOG_WRN("Could not send irq signal: %d", result);
    } else if (static_cast<std::size_t>(result) != sizeof(msg)) {
        LOG_WRN("Incomplete irq signal: %d of %u bytes", result,
                static_cast<unsigned int>(sizeof(msg)));
    }
}
