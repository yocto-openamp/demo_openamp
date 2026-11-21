#pragma once

#include "generated_irq_x19_7_struct.hpp"
#include "lib_rpmsg.hpp"
#include "messages_to_A53.hpp"

#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>

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
        // [us] The minimum time since the last wakeup of the sender thread
        // before a livesign is sent.
        uint64_t livesign_min_delay_us;
        // See messages_to_A53.hpp.
        commands::MSG_ID_M7_to_A53 message_id;
    };

    IrqThrottler(rpmsg::Endpoint &endpoint, const Config &config);

    IrqThrottler(const IrqThrottler &) = delete;
    IrqThrottler &operator=(const IrqThrottler &) = delete;

    // Called by the interrupt service routine: Updates the interrupt counters
    // and 'irq_timestamp_us_' and, if the rate limit is met, wakes the sender
    // thread ('rpmsg_send' may block and is not ISR-safe).
    void irq();

  private:
    static void thread_entry(void *self, void *, void *);
    void run();
    void send_signal(bool is_interrupt);
    uint64_t read_irq_timestamp_us();

    rpmsg::Endpoint *endpoint_;
    uint64_t irq_min_interval_us_;
    uint64_t livesign_min_delay_us_;
    commands::MSG_ID_M7_to_A53 message_id_;

    // Binary semaphore: irq() wakes the sender thread, bursts coalesce into
    // a single signal. A timeout while waiting triggers a livesign.
    struct k_sem sem_;
    // Written by irq() (ISR context) only. The sender thread reads it with an
    // optimistic retry guarded by 'irq_occurred_': the 64-bit read may tear
    // when an interrupt updates it mid-copy.
    uint64_t irq_timestamp_us_{0};
    atomic_t irq_occurred_{ATOMIC_INIT(0)};
    atomic_t irq_counter_{ATOMIC_INIT(0)};
    atomic_t irq_dropped_counter_{ATOMIC_INIT(0)};

    // The sender thread: the only context calling 'rpmsg_send'.
    struct k_thread thread_;
    K_KERNEL_STACK_MEMBER(stack_, 2048);
};
