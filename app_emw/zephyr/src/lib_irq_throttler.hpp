#pragma once

#include "generated_irq_x19_7_struct.hpp"
#include "lib_rpmsg.hpp"
#include "messages_to_A53.hpp"

#include <zephyr/kernel.h>
#include <zephyr/spinlock.h>

#include <cstdint>

// Forwards interrupt signals with minimal delay while limiting their rate.
// When signals are absent, periodic livesigns are sent instead.
// See lib_irq_throttler_AGENT.md.
class IrqThrottler {
  public:
    struct Config {
        // [us] The minimum interval between consecutive interrupts for an
        // interrupt signal to be forwarded. The previous interrupt counts
        // even if its signal was dropped.
        uint64_t irq_min_interval_us;
        // [us] The minimum time since the last signal before a livesign
        // is sent.
        uint64_t livesign_min_delay_us;
        // See messages_to_A53.hpp.
        commands::MSG_ID_M7_to_A53 message_id;
    };

    IrqThrottler(rpmsg::Endpoint &endpoint, const Config &config);

    IrqThrottler(const IrqThrottler &) = delete;
    IrqThrottler &operator=(const IrqThrottler &) = delete;

    // Called by the interrupt service routine: Updates the interrupt counters
    // and 'irq_timestamp_us' and, if the rate limit is met, defers the
    // interrupt signal to the system workqueue ('rpmsg_send' may block and is
    // not ISR-safe).
    void irq();

    // Called from main() at the 'poll_rate_s' interval: Sends a livesign if
    // no signal was sent for at least 'livesign_min_delay_us'.
    void poll();

  private:
    static void work_handler(struct k_work *work);
    void send_signal(const IrqX19_7_t &signal);

    rpmsg::Endpoint *endpoint_;
    uint64_t irq_min_interval_us_;
    uint64_t livesign_min_delay_us_;
    commands::MSG_ID_M7_to_A53 message_id_;

    struct k_work work_;
    // Serializes sends with the livesign due check, without blocking IRQs.
    struct k_mutex send_mutex_;
    // Protects the state shared between irq(), poll() and work_handler():
    // Safe in both ISR and thread context.
    struct k_spinlock lock_{};
    uint64_t irq_timestamp_us_{0};
    uint64_t signal_timestamp_us_{0};
    uint16_t irq_counter_{0};
    uint16_t irq_dropped_counter_{0};
    // The interrupt signal pending in the system workqueue.
    IrqX19_7_t pending_{};
};
