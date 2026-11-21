# IRQ Throttler

## Purpose and behavior

The IRQ Throttler is a statically allocated C++ class.

Interrupts should be handled and **forwarded with minimal delay**.

However, a rapid sequence of interrupts may overload the system. The IRQ Throttler
therefore **limits the rate** at which interrupt signals are sent.

When no signal has been sent for a longer time, the class will send
**periodic livesign** signals to indicate that it remains active. This also
reports the counters during a continuous sequence of dropped interrupts.


## Configuration

### Per-instance configuration

* `irq_min_interval_us` [us]: The minimum interval between sent interrupt
  signals. Further interrupts within this interval are counted but dropped.
* `livesign_min_delay_us` [us]: The minimum time since the last wakeup of the
  sender thread before a livesign is sent.
* `message_id`: See `messages_to_A53.hpp`

## Signal format

The `irq_signal` message contains the following fields:

* `irq_timestamp_us`: The timestamp at which the interrupt occurred.
* `irq_counter`: A counter incremented for each interrupt. It may wrap on
  overflow.
* `irq_dropped_counter`: A counter of the interrupts whose signals were
  dropped by the rate limit. It may wrap on overflow.
* `is_interrupt`: `true` for an interrupt signal and `false` for a livesign.

## Signal generation

### Interrupt signals

When an interrupt occurs, `irq()` records the current time in
`irq_timestamp_us`, increments `irq_counter` and wakes the sender thread. All
policy lives in the sender thread.

The sender thread applies the rate limit: an interrupt signal is sent if at
least `irq_min_interval_us` has elapsed since the last sent interrupt signal.
Otherwise the interrupt is dropped and reflected in `irq_dropped_counter`,
which the sender thread derives as `irq_counter` minus the number of sent
interrupt signals.

The last-send time is initialized to 0. The same interval check applies to
the first interrupt, using 0 as the previous send time.

Consequently, a continuous sequence of interrupts spaced closer together than
`irq_min_interval_us` produces one interrupt signal per `irq_min_interval_us`,
carrying the current counters.

### Livesign signals

The sender thread waits on its semaphore with a timeout of
`livesign_min_delay_us`. When the timeout expires - no interrupt signal woke
the thread for at least `livesign_min_delay_us` - a livesign is sent.
Livesign signals have `is_interrupt=false`. No separate timestamp
bookkeeping is kept: the semaphore wait itself measures the delay, so a
failed send does not shorten the interval until the next livesign.

A livesign contains the `irq_timestamp_us` of the most recent interrupt and
the current `irq_counter` and `irq_dropped_counter`, including interrupts
whose signals were dropped. Before the first interrupt, the livesign contains
the initial `irq_timestamp_us` value of 0. Every interrupt - including a
dropped one - wakes the sender thread and thereby postpones the next
livesign; during such a sequence, rate-limited interrupt signals are sent
instead.

## Implementation

### C++

The implementation consists of:

* `lib_irq_throttler.hpp`
* `lib_irq_throttler.cpp`

The class may be instantiated in `main()`, with its configuration passed to
the constructor. It should be statically allocated and must not allocate
memory from the heap using `malloc`.

### Interface

* `irq()`: Called by the interrupt service routine. It records
  `irq_timestamp_us`, increments `irq_counter` and wakes the sender thread.

### Interrupt and sender-thread concurrency

Each instance owns a dedicated sender thread, the only context that calls
`rpmsg_send`. Sends are therefore serialized without a mutex, and no
workqueue is used - `rpmsg_send` may block and is not ISR-safe, so blocking
the system workqueue would stall unrelated work items.

`irq()` is ISR-safe, non-blocking and policy-free: it records the state and
gives a binary semaphore. Bursts of interrupts coalesce into a single
wakeup. The sender thread waits on the semaphore with a timeout of
`livesign_min_delay_us`: taken means an interrupt occurred, a timeout means
a livesign is due. The rate limit and the dropped-count derivation use only
thread-local state.

The shared state is handled without locks:

* `irq_counter` is a Zephyr `atomic_t`, updated with `atomic_inc` and read
  with `atomic_get`. The counters are truncated to `uint16_t` when the
  message is built, which preserves the wrap semantics.
* `irq_timestamp_us` is 64-bit and written by `irq()` only. The Cortex-M7
  cannot read 64 bits atomically, so the sender thread uses an optimistic
  retry: it clears the `atomic_t` flag `irq_occurred`, copies the timestamp,
  and retries if the flag was set by an interrupt during the copy.

Accepted simplifications - these deviations only matter in rare burst or
error conditions:

* A livesign is due `livesign_min_delay_us` after the last wakeup of the
  sender thread, not after the last successful send.
* The counters in a signal may already include interrupts that arrived after
  the interrupt that triggered the wakeup.
* Every interrupt wakes the sender thread, even when its signal is then
  dropped by the rate limit: an interrupt storm costs one thread wakeup per
  interrupt.
* A failed send still counts as sent for the rate limit and the dropped
  count.

## Integration example

### Instance

Create an instance named `irq_throttler_timing_trig`.

### Interrupt source

The IrqX19_7 interrupt input at X19-7(SODIMM_22) is triggered on the
positive edge and calls `irq_throttler_timing_trig.irq()`.

There is a loopback from X19-6(SODIMM_20) to X19-7(SODIMM_22):

```bash
gpiomon SODIMM_22 &
gpioset --toggle=1000 SODIMM_20=1
497.762368651   falling "SODIMM_22"
498.762894224   rising  "SODIMM_22"
499.763356678   falling "SODIMM_22"
```

Use X19-6(SODIMM_20) to test the new class!

### Signal data model

* Add a `ModelIrqX19_7` class with members corresponding to `irq_signal` in
  `app_emw/linux/src/app_emw/datamodel/datamodels_emw.py`. The generated C++
  field types are:
  * `irq_timestamp_us`: `uint64_t`
  * `irq_counter`: `uint16_t`
  * `irq_dropped_counter`: `uint16_t`
  * `is_interrupt`: `bool`
* Add the model to the code generator in
  `app_emw/linux/src/app_emw/app/main_codegeneration.py`.
* Generate the `irq_signal` data structure by running
  `app_emw/run_0_codegeneration.sh`.
* Add handling for `ModelIrqX19_7` to the Linux message handler in
  `app_emw/linux/src/app_emw/lib/util_cmd_to_a53.py`, including deserialization
  of the signal.

### Message Id

Add a new message ID `IRQ_X19_7`.

app_emw/linux/src/app_emw/lib/util_cmd_to_a53.py
```python
# These must match util_messages_to_A53.py.
class MSG_ID_M7_to_A53(enum.IntEnum):
    STATUS = 1
    IMU_STATUS = 2
    IRQ_X19_7 = 3
```

app_emw/zephyr/src/messages_to_A53.hpp
```C++
// These must match util_messages_to_A53.py.
enum class MSG_ID_M7_to_A53 : uint8_t {
    STATUS = 1,
    IMU_STATUS = 2,
    IRQ_X19_7 = 3,
};
```
