import pathlib
import shutil
import subprocess
import textwrap

import pytest


def test_irq_throttler_livesigns(tmp_path: pathlib.Path) -> None:
    compiler = shutil.which("g++")
    if compiler is None:
        pytest.skip("g++ is required for the host-side IRQ throttler test")

    headers = {
        "zephyr/kernel.h": """
            #pragma once
            #include <cstddef>
            #include <cstdint>
            inline uint64_t test_now_us = 0;
            inline uint64_t k_cycle_get_64() { return test_now_us; }
            inline uint64_t k_cyc_to_us_near64(uint64_t value) { return value; }
            struct k_work { void (*handler)(k_work *); };
            inline k_work *test_pending = nullptr;
            inline void k_work_init(k_work *work, void (*handler)(k_work *)) {
                work->handler = handler;
            }
            inline int k_work_submit(k_work *work) { test_pending = work; return 0; }
            struct k_mutex {};
            #define K_FOREVER 0
            inline void k_mutex_init(k_mutex *) {}
            inline int k_mutex_lock(k_mutex *, int) { return 0; }
            inline int k_mutex_unlock(k_mutex *) { return 0; }
            #define CONTAINER_OF(ptr, type, member) \\
                ((type *)((char *)(ptr) - offsetof(type, member)))
        """,
        "zephyr/spinlock.h": """
            #pragma once
            struct k_spinlock {};
            using k_spinlock_key_t = int;
            inline k_spinlock_key_t k_spin_lock(k_spinlock *) { return 0; }
            inline void k_spin_unlock(k_spinlock *, k_spinlock_key_t) {}
        """,
        "zephyr/logging/log.h": """
            #pragma once
            #define LOG_MODULE_REGISTER(...)
            #define LOG_WRN(...)
        """,
        "generated_irq_x19_7_struct.hpp": """
            #pragma once
            #include <cstdint>
            struct __attribute__((packed)) IrqX19_7_t {
                uint64_t irq_timestamp_us;
                uint16_t irq_counter;
                uint16_t irq_dropped_counter;
                uint16_t is_interrupt;
            };
        """,
        "lib_rpmsg.hpp": """
            #pragma once
            #include <cstddef>
            #include <vector>
            namespace rpmsg {
            struct Endpoint {
                int result = 0;
                std::vector<std::vector<unsigned char>> messages;
                int send(const void *data, std::size_t size) {
                    if (result != 0) return result;
                    auto bytes = static_cast<const unsigned char *>(data);
                    messages.emplace_back(bytes, bytes + size);
                    return static_cast<int>(size);
                }
            };
            }
        """,
    }
    for name, content in headers.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content))

    test_source = tmp_path / "test.cpp"
    test_source.write_text(
        textwrap.dedent(
            """
            #include "lib_irq_throttler.hpp"
            #include "messages.hpp"
            #include <cassert>
            #include <cstring>

            IrqX19_7_t last_signal(const rpmsg::Endpoint &endpoint) {
                IrqX19_7_t signal{};
                const auto &message = endpoint.messages.back();
                assert(message.size() == sizeof(commands::msg_header) + sizeof(signal));
                std::memcpy(&signal, message.data() + sizeof(commands::msg_header),
                            sizeof(signal));
                return signal;
            }

            int main() {
                rpmsg::Endpoint endpoint;
                IrqThrottler throttler(endpoint, {50, 100,
                    commands::MSG_ID_M7_to_A53::IRQ_X19_7});

                test_now_us = 99;
                throttler.poll();
                assert(endpoint.messages.empty());
                test_now_us = 100;
                throttler.poll();
                assert(endpoint.messages.size() == 1);
                assert(!last_signal(endpoint).is_interrupt);
                throttler.poll();
                assert(endpoint.messages.size() == 1);

                test_now_us = 150;
                throttler.irq();
                assert(test_pending != nullptr);
                test_pending->handler(test_pending);
                assert(endpoint.messages.size() == 2);
                assert(last_signal(endpoint).is_interrupt);

                for (test_now_us = 160; test_now_us <= 240; test_now_us += 10)
                    throttler.irq();
                test_now_us = 249;
                throttler.poll();
                assert(endpoint.messages.size() == 2);
                test_now_us = 250;
                throttler.irq();
                throttler.poll();
                assert(endpoint.messages.size() == 3);
                auto livesign = last_signal(endpoint);
                assert(!livesign.is_interrupt);
                assert(livesign.irq_timestamp_us == 250);
                assert(livesign.irq_counter == 11);
                assert(livesign.irq_dropped_counter == 10);

                test_now_us = 350;
                endpoint.result = -1;
                throttler.poll();
                endpoint.result = 1;
                throttler.poll();
                assert(endpoint.messages.size() == 3);
                endpoint.result = 0;
                throttler.poll();
                assert(endpoint.messages.size() == 4);
                throttler.poll();
                assert(endpoint.messages.size() == 4);
            }
            """
        )
    )
    src = pathlib.Path(__file__).resolve().parents[2] / "zephyr" / "src"
    executable = tmp_path / "test_irq_throttler"
    subprocess.run(
        [
            compiler,
            "-std=c++17",
            "-I",
            str(tmp_path),
            "-I",
            str(src),
            str(src / "lib_irq_throttler.cpp"),
            str(test_source),
            "-o",
            str(executable),
        ],
        check=True,
    )
    subprocess.run([str(executable)], check=True)
