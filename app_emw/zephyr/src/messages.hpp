#pragma once

#include <cstdint>

namespace commands {

// Common header of every RPMsg message. This must match util_messages.py.
typedef struct __attribute__((packed)) {
    int16_t msg_id;
    int16_t msg_size; // Size of the whole message including this header.
} msg_header;

static_assert(sizeof(msg_header) == 4, "msg_header layout changed");

} // namespace commands
