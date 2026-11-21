#include "lib_irq_throttler.hpp"

#include "messages.hpp"

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include <cstddef>

LOG_MODULE_REGISTER(lib_irq_throttler);

namespace {

uint64_t timestamp_us() { return k_cyc_to_us_near64(k_cycle_get_64()); }

} // namespace

IrqThrottler::IrqThrottler(rpmsg::Endpoint &endpoint, const Config &config)
    : endpoint_(&endpoint),
      irq_min_interval_us_(config.irq_min_interval_us),
      livesign_min_delay_us_(config.livesign_min_delay_us),
      message_id_(config.message_id) {
    k_work_init(&work_, work_handler);
}

void IrqThrottler::irq() {
    const uint64_t now_us = timestamp_us();
    bool forward;

    k_spinlock_key_t key = k_spin_lock(&lock_);
    // The previous interrupt counts even if its signal was dropped.
    forward = (now_us - irq_timestamp_us_) >= irq_min_interval_us_;
    irq_counter_++;
    irq_timestamp_us_ = now_us;
    if (forward) {
        pending_ = {now_us, irq_counter_, irq_dropped_counter_, true};
    } else {
        irq_dropped_counter_++;
    }
    k_spin_unlock(&lock_, key);

    if (forward) {
        k_work_submit(&work_);
    }
}

void IrqThrottler::poll() {
    const uint64_t now_us = timestamp_us();

    k_spinlock_key_t key = k_spin_lock(&lock_);
    const bool send = (now_us - irq_timestamp_us_) >= livesign_min_delay_us_;
    const IrqX19_7_t livesign = {
        irq_timestamp_us_, irq_counter_, irq_dropped_counter_, false};
    k_spin_unlock(&lock_, key);

    if (send) {
        send_signal(livesign);
    }
}

void IrqThrottler::work_handler(struct k_work *work) {
    IrqThrottler &self = *CONTAINER_OF(work, IrqThrottler, work_);

    k_spinlock_key_t key = k_spin_lock(&self.lock_);
    const IrqX19_7_t signal = self.pending_;
    k_spin_unlock(&self.lock_, key);

    self.send_signal(signal);
}

void IrqThrottler::send_signal(const IrqX19_7_t &signal) {
    // Sent 1:1 over RPMsg: the msg_header followed by the irq_signal.
    struct __attribute__((packed)) {
        commands::msg_header header;
        IrqX19_7_t signal;
    } msg = {};
    msg.header.msg_id = static_cast<int16_t>(message_id_);
    msg.header.msg_size = sizeof(msg);
    msg.signal = signal;

    const int result = endpoint_->send(&msg, sizeof(msg));
    if (result < 0) {
        LOG_WRN("Could not send irq signal: %d", result);
    } else if (static_cast<std::size_t>(result) != sizeof(msg)) {
        LOG_WRN("Incomplete irq signal: %d of %u bytes", result,
                static_cast<unsigned int>(sizeof(msg)));
    }
}
