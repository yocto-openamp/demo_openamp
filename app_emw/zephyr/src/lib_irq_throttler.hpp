#pragma once

#include "generated_irq_x19_7_struct.hpp"
#include "lib_rpmsg.hpp"
#include "messages_to_A53.hpp"

#include <zephyr/kernel.h>
#include <zephyr/spinlock.h>

#include <cstdint>

// Forwards interrupt signals with minimal delay while limiting their rate.
// When interrupts are absent, periodic livesigns are sent instead.
// See lib_irq_throttler_AGENT.md.
class IrqThrottler {
  public:
    struct Config {
        // [s] The minimum interval between consecutive interrupts for an
        // interrupt signal to be forwarded. The previous interrupt counts
        // even if its signal was dropped.
        double irq_min_interval_s;
        // [s] The minimum time since the last interrupt before a livesign
        // is sent.
        double livesign_min_delay_s;
        // See messages_to_A53.hpp.
        commands::MSG_ID_M7_to_A53 message_id;
    };

    IrqThrottler(rpmsg::Endpoint &endpoint, const Config &config);

    IrqThrottler(const IrqThrottler &) = delete;
    IrqThrottler &operator=(const IrqThrottler &) = delete;

    // Called by the interrupt service routine: Updates 'irq_counter' and
    // 'irq_timestamp_us' and, if the rate limit is met, defers the interrupt
    // signal to the system workqueue ('rpmsg_send' may block and is not
    // ISR-safe).
    void irq();

    // Called from main() at the 'poll_rate_s' interval: Sends a livesign if
    // no interrupt occurred for at least 'livesign_min_delay_s'.
    void poll();

  private:
    static void work_handler(struct k_work *work);
    void send_signal(const IrqX19_7_t &signal);

    rpmsg::Endpoint *endpoint_;
    uint64_t irq_min_interval_us_;
    uint64_t livesign_min_delay_us_;
    commands::MSG_ID_M7_to_A53 message_id_;

    struct k_work work_;
    // Protects the state shared between irq(), poll() and work_handler():
    // Safe in both ISR and thread context.
    struct k_spinlock lock_{};
    uint64_t irq_timestamp_us_{0};
    uint16_t irq_counter_{0};
    // The interrupt signal pending in the system workqueue.
    IrqX19_7_t pending_{};
};
