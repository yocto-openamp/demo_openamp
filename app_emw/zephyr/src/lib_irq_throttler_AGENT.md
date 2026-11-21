# IRQ Throttler

## Purpose and behavior

The IRQ Throttler is a statically allocated C++ class.

Interrupts should be handled and **forwarded with minimal delay**.

However, a rapid sequence of interrupts may overload the system. The IRQ Throttler
therefore **limits the rate** at which interrupt signals are sent.

When interrupts are absent for a longer time
the class will send **periodic livesign** signals to indicate that it remains
active.


## Configuration

### Global configuration

* `poll_rate_s` [s]: The interval at which the main loop calls `poll()`. This will trigger livesigns.

### Per-instance configuration

* `irq_min_interval_s` [s]: The minimum interval between consecutive interrupts
  for an interrupt signal to be forwarded. The previous interrupt counts even
  if its signal was dropped.
* `livesign_min_delay_s` [s]: The minimum time since the last interrupt before
  a livesign is sent.
* `message_id`: See `messages_to_A53.hpp`

## Signal format

The `irq_signal` message contains the following fields:

* `irq_timestamp_us`: The timestamp at which the interrupt occurred.
* `irq_counter`: A counter incremented for each interrupt. It may wrap on
  overflow.
* `is_interrupt`: `true` for an interrupt signal and `false` for a livesign.

## Signal generation

### Interrupt signals

When an interrupt occurs, `irq()` compares the current time with the previous
`irq_timestamp_us` before updating it. It increments `irq_counter` and updates
`irq_timestamp_us` for every interrupt, including those whose signals are
dropped. The interrupt signal is sent only when at least
`irq_min_interval_s` has elapsed since the previous interrupt.

`irq_timestamp_us` is initialized to 0. The same interval check applies to
the first interrupt, using 0 as the previous timestamp.

Consequently, a continuous sequence of interrupts spaced closer together than
`irq_min_interval_s` will not produce further interrupt signals until an
interrupt follows a sufficiently long gap.

### Livesign signals

The main loop calls `poll()` at the `poll_rate_s` interval. A livesign is sent
if at least `livesign_min_delay_s` has elapsed since the last interrupt, as
recorded in `irq_timestamp_us`, including an interrupt whose signal was
dropped. Livesign signals have `is_interrupt=false`.

A livesign contains the `irq_timestamp_us` of the most recent interrupt and
the current `irq_counter`, including interrupts whose signals were dropped.
Before the first interrupt, the same delay check uses the initial
`irq_timestamp_us` value of 0; any livesign sent then contains that value.

## Implementation

### C++

The implementation consists of:

* `lib_irq_throttler.hpp`
* `lib_irq_throttler.cpp`

The class may be instantiated in `main()`, with its configuration passed to
the constructor. It should be statically allocated and must not allocate
memory from the heap using `malloc`.

### Interface

* `poll()`: Called from `main()` at the configured `poll_rate_s` interval.
  It checks whether a livesign should be sent.
* `irq()`: Called by the interrupt service routine. It checks the interval
  since the previous interrupt, updates `irq_counter` and `irq_timestamp_us`,
  and sends a signal if the interval meets the rate limit.

### Interrupt and main-loop concurrency

`poll()` can be interrupted by `irq()`. The implementation must protect shared
state using Zephyr primitives that are safe in both contexts. In particular,
`poll()` must read a consistent snapshot of `irq_timestamp_us` and
`irq_counter`, including when the timestamp cannot be read atomically on its
own.

Signal delivery from `irq()` must use an ISR-safe, non-blocking mechanism. If
the delivery mechanism is not ISR-safe, delivery must be deferred to a thread.
Do not hold a critical section across a potentially blocking send.

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

### Polling in `main.cpp`

The current `poll_rate_s` is based on the existing
`M7_STATUS_INTERVAL_MS(main.cpp)` constant:

```C++
    while (true) {
        // Sleep first to stay out of the Linux ping-pong on this channel.
        k_sleep(K_MSEC(M7_STATUS_INTERVAL_MS));
        send_m7_status();
        irq_throttler_timing_trig.poll();
    }
```

### Signal data model

* Add a `IrqX19_7` class with members corresponding to `irq_signal` in
  `app_emw/linux/src/app_emw/datamodel/datamodels_emw.py`. The generated C++
  field types are:
  * `irq_timestamp_us`: `uint64_t`
  * `irq_counter`: `uint16_t`
  * `is_interrupt`: `bool`
* Add the model to the code generator in
  `app_emw/linux/src/app_emw/app/main_codegeneration.py`.
* Generate the `irq_signal` data structure by running
  `app_emw/run_0_codegeneration.sh`.
* Add handling for `IrqX19_7` to the Linux message handler in
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
